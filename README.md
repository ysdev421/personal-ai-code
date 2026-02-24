# 🤖 Personal AI Partner

あなた専用の AI エージェント。あなたの人生データを学習し、購買相談から健康管理まで、すべてをサポートする個人用 AI パートナー。

## 📋 概要

Personal AI Partner は、以下の機能を持つローカル AI エージェントです：

- **ローカル LLM**：Ollama + Mistral 7B で、あなたの PC 上で完全に動作
- **個人データ管理**：購入履歴、健康情報、目標などを JSON で保存
- **リアルタイムチャット**：WebSocket でブラウザから即座に相談可能
- **知識蓄積**：会話履歴が自動で保存され、AI が学習
- **完全プライベート**：すべてのデータはあなたの PC に保存（外部に送信しない）

## 🚀 クイックスタート

### 前提条件

- Windows PC（Mac/Linux でも可）
- Python 3.14+
- 8GB 以上の RAM
- 20GB 以上の SSD 空き容量

### セットアップ（5 分）

#### 1. Ollama をインストール

```bash
# https://ollama.ai からダウンロード
# インストール完了後、PC を再起動
ollama --version
```

#### 2. Mistral モデルをダウンロード

```bash
ollama pull mistral
```

#### 3. Python ライブラリをインストール

```bash
cd C:\personal-ai-code
pip install fastapi uvicorn websockets python-dotenv streamlit
```

#### 4. 初期化

```bash
python init_chromadb.py
```

### 起動（3 つのターミナル）

**ターミナル 1：Ollama**
```bash
ollama serve
```

**ターミナル 2：バックエンド**
```bash
cd C:\personal-ai-code
python backend_server.py
```

**ターミナル 3：フロントエンド**
```bash
cd C:\personal-ai-code
python -m streamlit run frontend_ui.py
```

ブラウザで開く：
```
http://localhost:8501
```

## 📁 ファイル構成

```
personal-ai-code/
├── backend_server.py       # FastAPI バックエンドサーバー
├── frontend_ui.py          # Streamlit フロントエンド
├── init_chromadb.py        # 初期データセットアップ
├── requirements.txt        # 必要な Python ライブラリ
└── .env                    # 環境変数（Gmail API 設定用）

personal-ai-data/
└── data/
    ├── backup.json         # ナレッジベース（自動保存）
    ├── conversations.json  # 会話履歴（自動保存）
    └── weekly/
        └── week_*.md       # 週間サマリー（オプション）
```

## 💬 使い方

### 1. ブラウザでチャット

```
「椅子を買いたい」と入力

↓

AI が過去データを参照して返答

「あなたの腰痛を考慮すると、メッシュ素材の椅子がいいでしょう。
 前回のゲーミングチェア（硬め）での失敗を踏まえて...」
```

### 2. データが自動保存される

- チャット履歴 → `data/conversations.json`
- 購入情報 → `data/backup.json`

### 3. AI が学習

毎回の相談で、AI のナレッジベースが増える。
1 ヶ月後、精度が上がったと実感できます。

## 🔧 カスタマイズ

### あなたの情報を追加

`init_chromadb.py` の `initial_data` を編集：

```python
initial_data = {
    "documents": [
        "あなたの基本情報を記入",
        "健康情報を記入",
        # ... その他
    ]
}
```

実行：
```bash
python init_chromadb.py
```

### AI の性格を変更

`backend_server.py` の `process_user_message()` 内のプロンプトを編集：

```python
prompt = f"""あなたはユーザーの個人用 AI パートナーです。
【ここにあなたの指示を追加】
ユーザーの過去データ：
{context}
...
"""
```

## 📊 機能

### 現在実装済み

- ✅ チャットインターフェース
- ✅ ローカル LLM（Ollama）
- ✅ ナレッジベース（JSON ファイル）
- ✅ 会話履歴の自動保存
- ✅ リアルタイム応答

### 今後実装可能

- ⬜️ Gmail 連携（自動購入検知）
- ⬜️ クレジットカード CSV 自動取得
- ⬜️ Google Calendar 連携
- ⬜️ Apple Health 連携
- ⬜️ 定期バックアップ（Google Drive）
- ⬜️ 週間サマリー自動生成
- ⬜️ LINE 通知機能
- ⬜️ トリガーベースのプロアクティブ提案

## 🔐 セキュリティ

- **完全ローカル**：すべてのデータは あなたの PC に保存
- **外部送信なし**：Anthropic / OpenAI / Google に一切データを送らない
- **オープンソース**：使用しているすべてのライブラリがオープンソース
- **カスタマイズ可能**：ソースコードを完全にコントロール可能

## ⚠️ トラブルシューティング

### Q: メッセージを送っても返答が来ない

**A:** 3 つのターミナルが全部起動しているか確認

```bash
# ターミナル 2 でバックエンド確認
INFO:     Uvicorn running on http://0.0.0.0:8000

# ターミナル 1 で Ollama 確認
# エラーが出ていないか確認
```

### Q: Ollama が遅い

**A:** 正常です。ローカル LLM は クラウド API より遅い（5～15 秒）

### Q: Python 3.14 でエラーが出る

**A:** Python 3.11 にダウングレード推奨

```bash
# https://www.python.org/downloads/release/python-3110/
```

## 📈 今後の拡張

このプロジェクトは以下のように拡張可能です：

1. **データ連携**
   - Amazon メール自動検知
   - クレジットカード支出分析
   - Google Calendar スケジュール認識

2. **AI 機能**
   - 長期記憶の拡張
   - パターン認識（「あなたは 3 月は疲れてる傾向」）
   - プロアクティブ提案（「来月はこれを買うといいよ」）

3. **バックアップ**
   - GitHub への自動同期
   - Google Drive へのバックアップ
   - 複数デバイスでの同期

## 🙏 謝辞

このプロジェクトは以下を使用しています：

- **Ollama**：ローカル LLM の実行
- **Mistral 7B**：AI エンジン
- **FastAPI**：バックエンドサーバー
- **Streamlit**：フロントエンド UI
- **Python**：プログラミング言語

## 📝 ライセンス

MIT License

## 📞 サポート

問題が発生した場合：

1. バックエンドのターミナルを確認（エラーメッセージを見る）
2. Ollama が動いているか確認
3. ポート 8000 / 8501 が被っていないか確認

## 🎯 次のステップ

1. **毎日使う**：データが貯まるほど AI が賢くなる
2. **1 ヶ月後**：AI の提案の精度が上がったと実感
3. **3 ヶ月後**：「あなたの専用 AI パートナー」として完成

---

**楽しい AI パートナーライフを！🤖✨**
