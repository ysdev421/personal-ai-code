from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# 環境変数読み込み
load_dotenv()

# Flask アプリ初期化
app = Flask(__name__)

# LINE API 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Ollama LLM 初期化
llm = Ollama(model="mistral")

# Chromadb 初期化（ナレッジベース）
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

# または既存コレクションを取得
try:
    collection = chroma_client.get_collection(name="user_knowledge")
except:
    collection = chroma_client.create_collection(name="user_knowledge")

# システムプロンプト
SYSTEM_PROMPT = """
あなたはユーザーの個人用 AI パートナーです。
ユーザーの過去データ（購入履歴、健康情報、好みなど）を踏まえて、
実用的で具体的なアドバイスをしてください。

以下の情報を参考にしてください：
{context}

ユーザーの質問に対して、親友のような温かいトーンで、
かつ論理的に回答してください。
"""

def search_knowledge_base(query: str) -> str:
    """Chromadb からユーザー情報を検索"""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        if results and results['documents']:
            context = "\n".join(results['documents'][0])
            return context
        else:
            return "（記録されたデータなし）"
    except Exception as e:
        print(f"検索エラー: {e}")
        return ""

def generate_response(user_input: str) -> str:
    """ユーザー入力に対して AI が返答を生成"""
    
    # 1. ナレッジベースから関連情報を検索
    context = search_knowledge_base(user_input)
    
    # 2. プロンプト作成
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=SYSTEM_PROMPT + "\n質問：{question}\n回答："
    )
    
    formatted_prompt = prompt.format(context=context, question=user_input)
    
    # 3. LLM に処理
    response = llm(formatted_prompt)
    
    return response

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhook エンドポイント"""
    
    # リクエストの署名検証
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """LINE メッセージハンドラー"""
    
    user_input = event.message.text
    user_id = event.source.user_id
    
    print(f"ユーザー: {user_id} が '{user_input}' と送信")
    
    # AI が返答生成
    try:
        response_text = generate_response(user_input)
    except Exception as e:
        response_text = f"申し訳ありません。エラーが発生しました: {str(e)}"
    
    # LINE に返答を送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_text)
    )
    
    # 会話をナレッジベースに保存（学習）
    try:
        collection.add(
            ids=[f"conversation_{event.timestamp}"],
            documents=[f"質問: {user_input}\n回答: {response_text}"],
            metadatas=[{"type": "conversation", "user_id": user_id}]
        )
    except Exception as e:
        print(f"データベース保存エラー: {e}")

if __name__ == '__main__':
    # Flask サーバー起動（localhost:5000）
    app.run(host='0.0.0.0', port=5000, debug=False)
