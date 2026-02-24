"""
Personal AI Partner - セットアップ & 実行ガイド
"""

# ════════════════════════════════════════════════════════════
# 【準備】ファイル構成
# ════════════════════════════════════════════════════════════

"""
~/personal_ai/
├── backend_server.py          ← FastAPI サーバー
├── frontend_ui.py             ← Streamlit フロントエンド
├── init_chromadb.py           ← DB 初期化（既存）
├── gmail_extractor.py         ← メール自動抽出（既存）
│
├── .env                       ← 環境変数
├── requirements.txt           ← ライブラリ一覧
├── credentials.json           ← Gmail API キー
│
├── chroma_data/              ← ベクトル DB（自動作成）
│   └── ...
│
└── cron.log                   ← ログファイル

"""

# ════════════════════════════════════════════════════════════
# 【Step 1】必要なライブラリをインストール
# ════════════════════════════════════════════════════════════

"""
ターミナルで以下を実行：

# 基本ライブラリ（既に入ってる可能性が高い）
pip install fastapi uvicorn websockets python-dotenv

# 追加ライブラリ
pip install streamlit apscheduler langchain chromadb ollama

# 全部インストール
pip install fastapi uvicorn websockets python-dotenv \
            streamlit apscheduler langchain chromadb ollama \
            google-auth-oauthlib google-auth-httplib2 google-api-python-client

requirements.txt 作成：

fastapi==0.104.1
uvicorn==0.24.0
websockets==12.0
python-dotenv==1.0.0
streamlit==1.28.0
apscheduler==3.10.0
langchain==0.1.0
chromadb==0.4.0
ollama==0.0.1
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.2.0
google-api-python-client==2.100.0

"""

# ════════════════════════════════════════════════════════════
# 【Step 2】環境変数設定 (.env)
# ════════════════════════════════════════════════════════════

"""
~/personal_ai/.env を作成：

# Gmail API
GMAIL_CREDENTIALS=./credentials.json

# 今後 LINE を使う場合のため（現在は不要）
# LINE_CHANNEL_ACCESS_TOKEN=xxxx
# LINE_CHANNEL_SECRET=xxxx
"""

# ════════════════════════════════════════════════════════════
# 【Step 3】Ollama セットアップ確認
# ════════════════════════════════════════════════════════════

"""
Ollama が動いてることを確認：

ターミナルで：
ollama serve

→ サーバーが起動するはず

別のターミナルで確認：
ollama list

→ mistral が表示されればOK
"""

# ════════════════════════════════════════════════════════════
# 【Step 4】Chromadb 初期化（初回のみ）
# ════════════════════════════════════════════════════════════

"""
ターミナルで：

cd ~/personal_ai
python init_chromadb.py

出力例：
✅ profile_basic を登録しました
✅ health_info を登録しました
...
登録完了！
"""

# ════════════════════════════════════════════════════════════
# 【Step 5】Gmail API セットアップ（初回のみ）
# ════════════════════════════════════════════════════════════

"""
1. https://console.cloud.google.com にアクセス
2. 新しいプロジェクト作成
3. Gmail API を検索して「有効にする」
4. 認証情報 → OAuth 2.0（デスクトップアプリ）を作成
5. credentials.json をダウンロード
6. ~/personal_ai/ に配置

初回実行：

ターミナルで：
python gmail_extractor.py

→ ブラウザが開く
→ Google アカウントでログイン
→ 許可をクリック
→ token.json が作成される

完了！
"""

# ════════════════════════════════════════════════════════════
# 【Step 6】バックエンドサーバー起動
# ════════════════════════════════════════════════════════════

"""
ターミナル 1 を開く：

cd ~/personal_ai
python backend_server.py

出力例：
INFO:     Uvicorn running on http://0.0.0.0:8000

サーバーが起動したら、ブラウザで確認：
http://localhost:8000/health

出力例：
{
  "status": "ok",
  "timestamp": "2025-02-24T...",
  "connected_clients": 0
}

このままターミナル 1 は開いておく。
"""

# ════════════════════════════════════════════════════════════
# 【Step 7】フロントエンド起動
# ════════════════════════════════════════════════════════════

"""
ターミナル 2 を開く：

cd ~/personal_ai
streamlit run frontend_ui.py

出力例：
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501

ブラウザで http://localhost:8501 を開く

→ 🤖 Personal AI Partner が表示される

サイドバーで「接続中」と表示されればOK
"""

# ════════════════════════════════════════════════════════════
# 【Step 8】テスト実行
# ════════════════════════════════════════════════════════════

"""
1. ブラウザで http://localhost:8501 を開く

2. 入力欄に「椅子を買いたい」と入力して送信

3. AI のアバターが 🤔 に変わる

4. 処理ステップが表示される
   - テキスト解析中...
   - データ検索中...
   - 回答生成中...

5. AI が返答する
   例）「メッシュ素材の椅子がいいでしょう...」

完成！
"""

# ════════════════════════════════════════════════════════════
# 【Step 9】トリガーのテスト
# ════════════════════════════════════════════════════════════

"""
朝のあいさつトリガーをテストするには：

backend_server.py の以下の部分を編集：

# 現在：
scheduler.add_job(
    morning_greeting,
    'cron',
    hour=8,
    minute=0,
    name='morning_greeting'
)

# テスト用に変更（1分後に実行）：
scheduler.add_job(
    morning_greeting,
    'interval',
    seconds=60,
    name='morning_greeting'
)

サーバーを再起動して、60秒待つと
トリガーメッセージが表示される。

テスト完了後は元に戻す。
"""

# ════════════════════════════════════════════════════════════
# 【トラブルシューティング】
# ════════════════════════════════════════════════════════════

"""
❌ WebSocket 接続失敗
原因：バックエンドが起動していない
対策：ターミナル 1 で backend_server.py が動いてるか確認

❌ Ollama にアクセスできない
原因：Ollama サーバーが起動していない
対策：別ターミナルで `ollama serve` を実行

❌ Gmail 連携できない
原因：credentials.json が見つからない
対策：Google Cloud Console で credentials.json をダウンロード

❌ メッセージが表示されない
原因：Chromadb に初期データがない
対策：init_chromadb.py を実行

❌ Streamlit が遅い
原因：PC のスペック不足
対策：バックグラウンドアプリを閉じる
"""

# ════════════════════════════════════════════════════════════
# 【本番環境へのデプロイ】
# ════════════════════════════════════════════════════════════

"""
VPS（Vultr $3/月）にデプロイする場合：

【ステップ 1】VPS レンタル
- Vultr.com で登録
- Ubuntu 22.04 で $3/月プラン選択
- SSH キーで接続

【ステップ 2】VPS に必要なツールをインストール
ssh root@<VPS IP>

apt update && apt upgrade -y
apt install -y python3-pip python3-venv git

【ステップ 3】プロジェクトをクローン
git clone <あなたのリポジトリ> personal_ai
cd personal_ai

【ステップ 4】環境構築
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

【ステップ 5】Ollama インストール
curl https://ollama.ai/install.sh | sh
ollama pull mistral

【ステップ 6】バックエンド起動（バックグラウンド）
nohup python backend_server.py > backend.log 2>&1 &

【ステップ 7】Streamlit 起動（バックグラウンド）
nohup streamlit run frontend_ui.py --server.port 8501 > frontend.log 2>&1 &

【ステップ 8】Nginx で HTTPS 設定
# 省略（複雑なので必要になったら聞いて）

これで 24/7 動作します。
"""

# ════════════════════════════════════════════════════════════
# 【実行フロー】（日々の使い方）
# ════════════════════════════════════════════════════════════

"""
【毎日】

朝：
  ターミナル 1 でバックエンドを起動
  > cd ~/personal_ai && python backend_server.py
  
  ターミナル 2 でフロントエンドを起動
  > cd ~/personal_ai && streamlit run frontend_ui.py
  
  ブラウザで http://localhost:8501 を開く

日中：
  ブラウザで相談したいことを入力
  AI が返答する
  トリガーメッセージが自動で来る

夜：
  相談内容が Chromadb に貯まっている
  Gmail から自動で購入情報が取得されている
  AI が学習している

就寝前：
  Ctrl+C でサーバーを停止（またはつけっぱなし）

【毎週日曜 21:00】
  Gmail から購入履歴の自動抽出
  クレジットカード CSV の自動取得
  Chromadb にデータが追加

【毎月】
  バックアップ実行
  """

# ════════════════════════════════════════════════════════════
# 【次のステップ】
# ════════════════════════════════════════════════════════════

"""
MVP 完成後のカスタマイズ：

【すぐにできる】
1. init_chromadb.py であなたの情報をもっと詳しく入力
2. backend_server.py の トリガーをカスタマイズ
3. frontend_ui.py の色・デザインを変更

【1週間で実装】
1. Amazon メール自動抽出を完全に動かす
2. クレジットカード CSV の自動取得
3. グラフ表示（支出、健康データなど）

【2週間で実装】
1. LINE 通知機能を追加
2. スマホ対応を完全化
3. VPS にデプロイ

【1ヶ月で実装】
1. React でもっと高度な UI を作成
2. 複数デバイス同期
3. AI の「性格」をカスタマイズ
"""

if __name__ == "__main__":
    print("""
    ════════════════════════════════════════════════════════════
    Personal AI Partner セットアップガイド
    ════════════════════════════════════════════════════════════
    
    【実行順序】
    
    Step 1: pip install -r requirements.txt
    Step 2: .env を設定
    Step 3: ollama serve（別ターミナル）
    Step 4: python init_chromadb.py
    Step 5: python gmail_extractor.py
    Step 6: python backend_server.py（ターミナル 1）
    Step 7: streamlit run frontend_ui.py（ターミナル 2）
    Step 8: ブラウザで http://localhost:8501 を開く
    
    完了！
    ════════════════════════════════════════════════════════════
    """)
