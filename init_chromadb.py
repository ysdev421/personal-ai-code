"""
Chromadb 初期化スクリプト（Python 3.14 対応版）
chromadb の代わりに JSON ファイルで管理
"""

import json
import os
from datetime import datetime

# data フォルダとファイル設定
DATA_DIR = "./data"
BACKUP_FILE = os.path.join(DATA_DIR, "backup.json")

# data フォルダがなければ作成
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"📁 ディレクトリ作成: {DATA_DIR}")

# 初期データ
initial_data = {
    "timestamp": datetime.now().isoformat(),
    "documents": [
        """ユーザーの基本情報：
- 主な悩み：腰痛が時々ある
- 生活スタイル：在宅勤務が主
- 好みの色：黒系
- 購入傾向：長く使えるものを重視
- 予算意識：3万円前後が目安""",
        
        """健康に関する情報：
- 腰痛あり（月1～2回程度）
- 運動習慣：週2～3回
- 睡眠：6～7時間
- 姿勢：デスク作業が多い""",
        
        """過去の購入履歴：
- ゲーミングチェア（1年前、硬め、腰痛悪化）→ 失敗
- メッシュ素材のオフィスチェア（3年前、快適）→ 成功
- 立つデスク用クッション（半年前）→ 効果あり

教訓：硬い素材は避けるべき、メッシュ素材が最適""",
        
        """あなたの好みとこだわり：
- 日本ブランドより信頼性
- Amazon レビュー 4.5 以上を重視
- デザインより機能性
- 長期保証があると安心
- サステナビリティに少し関心"""
    ],
    "metadatas": [
        {"type": "profile", "category": "basic"},
        {"type": "health"},
        {"type": "purchase_history"},
        {"type": "preferences"}
    ]
}

# JSON ファイルに保存
print("初期データを登録中...")

try:
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    print("✅ profile_basic を登録しました")
    print("✅ health_info を登録しました")
    print("✅ past_purchases を登録しました")
    print("✅ preferences を登録しました")
    
    print("\n登録完了！")
    print(f"📁 データファイル: {BACKUP_FILE}")
    print(f"📊 ドキュメント数: {len(initial_data['documents'])}")
    
    # テスト検索
    print("\n--- テスト検索 ---")
    test_query = "椅子について"
    print(f"クエリ: '{test_query}'")
    print("検索結果:")
    count = 0
    for i, doc in enumerate(initial_data['documents']):
        if "椅子" in doc or "メッシュ" in doc or "購入" in doc:
            print(f"\n{count+1}. {doc[:100]}...")
            count += 1
    
    if count == 0:
        print("検索結果なし")

except Exception as e:
    print(f"❌ エラー: {e}")
