import chromadb
from chromadb.config import Settings
import json
from datetime import datetime

# Chromadb 初期化
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

try:
    collection = chroma_client.get_collection(name="user_knowledge")
except:
    collection = chroma_client.create_collection(name="user_knowledge")

# あなたの基本情報を登録
initial_data = [
    {
        "id": "profile_basic",
        "document": """
        ユーザーの基本情報：
        - 主な悩み：腰痛が時々ある
        - 生活スタイル：在宅勤務が主
        - 好みの色：黒系
        - 購入傾向：長く使えるものを重視
        - 予算意識：3万円前後が目安
        """,
        "metadata": {"type": "profile", "category": "basic"}
    },
    {
        "id": "health_info",
        "document": """
        健康に関する情報：
        - 腰痛あり（月1～2回程度）
        - 運動習慣：週2～3回
        - 睡眠：6～7時間
        - 姿勢：デスク作業が多い
        """,
        "metadata": {"type": "health"}
    },
    {
        "id": "past_purchases",
        "document": """
        過去の購入履歴：
        - ゲーミングチェア（1年前、硬め、腰痛悪化）→ 失敗
        - メッシュ素材のオフィスチェア（3年前、快適）→ 成功
        - 立つデスク用クッション（半年前）→ 効果あり
        
        教訓：硬い素材は避けるべき、メッシュ素材が最適
        """,
        "metadata": {"type": "purchase_history"}
    },
    {
        "id": "preferences",
        "document": """
        あなたの好みとこだわり：
        - 日本ブランドより信頼性
        - Amazon レビュー 4.5 以上を重視
        - デザインより機能性
        - 長期保証があると安心
        - サステナビリティに少し関心
        """,
        "metadata": {"type": "preferences"}
    }
]

# データベースに登録
print("初期データを登録中...")
for item in initial_data:
    try:
        collection.add(
            ids=[item["id"]],
            documents=[item["document"]],
            metadatas=[item["metadata"]]
        )
        print(f"✅ {item['id']} を登録しました")
    except Exception as e:
        print(f"❌ {item['id']} のエラー: {e}")

print("\n登録完了！")
print(f"コレクション内のアイテム数: {collection.count()}")

# テスト検索
print("\n--- テスト検索 ---")
test_query = "椅子について"
results = collection.query(query_texts=[test_query], n_results=2)

if results['documents']:
    print(f"クエリ: '{test_query}'")
    print("検索結果:")
    for i, doc in enumerate(results['documents'][0]):
        print(f"\n{i+1}. {doc[:100]}...")
else:
    print("検索結果なし")
