"""
FastAPI バックエンドサーバー
WebSocket + トリガーエンジン
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Set
import logging
# apscheduler は Python 3.14 非対応のため、後で実装
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langchain.llms import Ollama
import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

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
                logger.info(f"メッセージ送信: {message['type']}")
            except Exception as e:
                logger.error(f"送信失敗: {e}")
                disconnected.append(connection)
        
        # 切断されたクライアントを削除
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

# LLM + DB 初期化
llm = Ollama(model="mistral")
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

try:
    collection = chroma_client.get_collection(name="user_knowledge")
except:
    collection = chroma_client.create_collection(name="user_knowledge")

# スケジューラー（Python 3.14 非対応のため後で実装）
# scheduler = AsyncIOScheduler()

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
    
    try:
        results = collection.query(
            query_texts=[user_input],
            n_results=3
        )
        context = "\n".join(results['documents'][0]) if results['documents'] else ""
    except:
        context = ""
    
    await asyncio.sleep(0.5)
    
    # ステップ 3: LLM で回答生成
    await manager.broadcast({
        'type': 'thinking',
        'step': 'generating',
        'message': '回答生成中...'
    })
    
    try:
        prompt = f"""
        あなたはユーザーの個人用 AI パートナーです。
        ユーザーの過去データを踏まえて、実用的で具体的なアドバイスをしてください。
        
        ユーザーのデータ：
        {context}
        
        ユーザーの質問：{user_input}
        
        回答：
        """
        
        response_text = llm(prompt)
    except Exception as e:
        logger.error(f"LLM エラー: {e}")
        response_text = "申し訳ありません。エラーが発生しました。"
    
    await asyncio.sleep(0.5)
    
    # 会話を Chromadb に保存（学習）
    try:
        collection.add(
            ids=[f"conversation_{datetime.now().timestamp()}"],
            documents=[f"質問: {user_input}\n回答: {response_text}"],
            metadatas=[{"type": "conversation"}]
        )
    except Exception as e:
        logger.error(f"DB 保存エラー: {e}")
    
    # レスポンス作成
    return {
        'type': 'response',
        'role': 'ai',
        'content': response_text,
        'timestamp': datetime.now().isoformat()
    }

# ────────────────────────────────────────
# トリガーエンジン
# ────────────────────────────────────────

async def send_trigger_message(trigger_type: str, content: str, metadata: dict = None):
    """トリガーメッセージをクライアントに送信"""
    message = {
        'type': 'trigger',
        'trigger_type': trigger_type,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata or {}
    }
    await manager.broadcast(message)
    logger.info(f"[TRIGGER] {trigger_type}: {content}")

# 【トリガー 1】毎日朝 8:00
async def morning_greeting():
    """朝のあいさつ"""
    content = "おはようございます！今日の体調はどうですか？"
    await send_trigger_message('morning', content)

# 【トリガー 2】最後の相談から 3 日経った
async def long_silence_trigger():
    """長時間相談がない"""
    # TODO: 最後の相談時刻を管理
    content = "最近相談がないですね。何か困ってることはありませんか？"
    await send_trigger_message('silence', content)

# 【トリガー 3】毎週月曜（支出確認）
async def weekly_summary():
    """週間サマリー"""
    content = "今週の支出、確認しましたか？食費が多めですね。"
    await send_trigger_message('weekly', content)

# 【トリガー 4】Amazon メール受信を監視
async def monitor_purchases():
    """購入トリガー（実装例）"""
    # TODO: Gmail API で Amazon メールを監視
    # 新しい購入があったら：
    # await send_trigger_message('purchase', 'メッセージ', {'product': '商品名'})
    pass

# 【トリガー 5】データ異常検知
async def detect_anomalies():
    """データパターン異常検知"""
    # TODO: Chromadb から過去データを分析
    # 異常があったら：
    # await send_trigger_message('alert', 'メッセージ')
    pass

# ────────────────────────────────────────
# スケジューラー設定
# ────────────────────────────────────────

def setup_scheduler():
    """スケジューラーをセットアップ"""
    
    # 時間ベースのトリガー
    scheduler.add_job(
        morning_greeting,
        'cron',
        hour=8,
        minute=0,
        name='morning_greeting'
    )
    
    scheduler.add_job(
        weekly_summary,
        'cron',
        day_of_week='mon',
        hour=9,
        minute=0,
        name='weekly_summary'
    )
    
    # 定期実行のトリガー
    scheduler.add_job(
        long_silence_trigger,
        'interval',
        minutes=30,
        name='long_silence_check'
    )
    
    scheduler.add_job(
        monitor_purchases,
        'interval',
        minutes=5,
        name='purchase_monitor'
    )
    
    scheduler.add_job(
        detect_anomalies,
        'interval',
        hours=1,
        name='anomaly_detection'
    )
    
    logger.info("スケジューラーセットアップ完了")

# ────────────────────────────────────────
# アプリケーション起動
# ────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("サーバー起動...")
    # スケジューラーは Python 3.14 非対応のため後で実装
    # setup_scheduler()
    # scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("サーバー停止...")
    # scheduler.shutdown()

# ────────────────────────────────────────
# ヘルスチェック
# ────────────────────────────────────────

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
