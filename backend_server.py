"""
FastAPI バックエンドサーバー - シンプル版
Python 3.14 対応（langchain・apscheduler なし）
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
from typing import Set
import logging
import subprocess

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI アプリ初期化
app = FastAPI(title="Personal AI Partner API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────
# グローバル設定
# ────────────────────────────────────────

# WebSocket 接続管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"クライアント接続。現在接続数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"クライアント切断。現在接続数: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """全接続クライアントにメッセージをブロードキャスト"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"送信失敗: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_specific(self, websocket: WebSocket, message: dict):
        """特定のクライアントにメッセージを送信"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"送信失敗: {e}")
            self.disconnect(websocket)

manager = ConnectionManager()

# ────────────────────────────────────────
# Ollama インタフェース
# ────────────────────────────────────────

def call_ollama(prompt: str) -> str:
    """Ollama を直接呼び出して応答を生成"""
    try:
        # ollama cli で Mistral を呼び出す
        result = subprocess.run(
            ['ollama', 'run', 'mistral', prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.error(f"Ollama エラー: {result.stderr}")
            return "申し訳ありません。AI エンジンに問題が発生しました。"
    
    except subprocess.TimeoutExpired:
        return "申し訳ありません。応答がタイムアウトしました。"
    except Exception as e:
        logger.error(f"Ollama 呼び出しエラー: {e}")
        return f"エラーが発生しました: {str(e)}"

# ────────────────────────────────────────
# ナレッジベース（JSON ファイルベース）
# ────────────────────────────────────────

def search_knowledge_base(query: str, max_results: int = 3) -> str:
    """簡単なキーワード検索"""
    try:
        with open('./data/backup.json', 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
    except Exception as e:
        logger.error(f"ナレッジベース読み込みエラー: {e}")
        return ""
    
    if not knowledge.get('documents'):
        return ""
    
    # キーワードマッチングで検索
    results = []
    for doc in knowledge['documents']:
        # クエリに含まれるキーワードが doc に含まれるか確認
        keywords = query.split()
        match_count = sum(1 for kw in keywords if kw in doc)
        
        if match_count > 0:
            results.append((match_count, doc))
    
    # マッチ度でソート
    results.sort(reverse=True)
    
    # 上位の結果を返す
    context = "\n".join([doc for _, doc in results[:max_results]])
    return context

# ────────────────────────────────────────
# メッセージ処理
# ────────────────────────────────────────

async def process_user_message(message: dict) -> dict:
    """ユーザーメッセージを処理して AI が返答"""
    
    user_input = message.get('content', '')
    
    logger.info(f"処理開始: {user_input}")
    
    # ステップ 1: テキスト解析
    await manager.broadcast({
        'type': 'thinking',
        'step': 'analyzing',
        'message': 'テキスト解析中...'
    })
    await asyncio.sleep(0.5)
    
    # ステップ 2: ナレッジベース検索
    await manager.broadcast({
        'type': 'thinking',
        'step': 'searching',
        'message': 'データ検索中...'
    })
    
    context = search_knowledge_base(user_input)
    await asyncio.sleep(0.5)
    
    # ステップ 3: LLM で回答生成
    await manager.broadcast({
        'type': 'thinking',
        'step': 'generating',
        'message': '回答生成中...'
    })
    
    prompt = f"""あなたはユーザーの個人用 AI パートナーです。
ユーザーの過去データを踏まえて、実用的で具体的なアドバイスをしてください。

ユーザーのデータ：
{context}

ユーザーの質問：{user_input}

回答："""
    
    response_text = call_ollama(prompt)
    
    await asyncio.sleep(0.5)
    
    # 会話をファイルに保存
    try:
        conversation = {
            'type': 'conversation',
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'ai_response': response_text
        }
        
        # conversations.json に追加
        try:
            with open('./data/conversations.json', 'r', encoding='utf-8') as f:
                conversations = json.load(f)
        except:
            conversations = {'conversations': []}
        
        conversations['conversations'].append(conversation)
        
        with open('./data/conversations.json', 'w', encoding='utf-8') as f:
            json.dump(conversations, f, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"会話保存エラー: {e}")
    
    # レスポンス作成
    return {
        'type': 'response',
        'role': 'ai',
        'content': response_text,
        'timestamp': datetime.now().isoformat()
    }

# ────────────────────────────────────────
# WebSocket エンドポイント
# ────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket エンドポイント"""
    await manager.connect(websocket)
    
    try:
        while True:
            # クライアントからのメッセージ受信
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.info(f"受信: {message}")
            
            # メッセージ処理
            response = await process_user_message(message)
            
            # クライアントに返答
            await manager.send_to_specific(websocket, response)
    
    except Exception as e:
        logger.error(f"WebSocket エラー: {e}")
    finally:
        manager.disconnect(websocket)

# ────────────────────────────────────────
# ヘルスチェック
# ────────────────────────────────────────

@app.post("/chat")
async def chat_endpoint(message: dict):
    """チャットエンドポイント（HTTP POST）"""
    response = await process_user_message(message)
    return response

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'connected_clients': len(manager.active_connections)
    }

# ────────────────────────────────────────
# メイン実行
# ────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    logger.info("FastAPI サーバー起動...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
