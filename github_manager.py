"""
GitHub 統合モジュール
Chromadb データを GitHub に自動バックアップ
"""

import os
import json
import subprocess
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GitHubManager:
    """GitHub 連携マネージャー"""
    
    def __init__(self, repo_path: str = "."):
        """
        初期化
        
        Args:
            repo_path: GitHub リポジトリのパス
        """
        self.repo_path = repo_path
        self.data_dir = os.path.join(repo_path, "data")
        
        # data/ ディレクトリがなければ作成
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"ディレクトリ作成: {self.data_dir}")
    
    def export_chromadb_to_json(self, collection) -> dict:
        """
        Chromadb のデータを JSON 形式でエクスポート
        
        Args:
            collection: Chromadb コレクション
        
        Returns:
            dict: エクスポートされたデータ
        """
        try:
            all_data = collection.get()
            
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'total_documents': len(all_data['documents']),
                'documents': all_data['documents'],
                'metadatas': all_data['metadatas'],
                'ids': all_data['ids']
            }
            
            logger.info(f"Chromadb をエクスポート: {len(all_data['documents'])} 件")
            return export_data
        
        except Exception as e:
            logger.error(f"エクスポートエラー: {e}")
            return {}
    
    def save_backup(self, data: dict, filename: str = "backup.json") -> bool:
        """
        バックアップデータをファイルに保存
        
        Args:
            data: 保存するデータ
            filename: ファイル名
        
        Returns:
            bool: 成功したか
        """
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"バックアップ保存: {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")
            return False
    
    def commit_and_push(self, message: Optional[str] = None) -> bool:
        """
        Git コミット＆プッシュ
        
        Args:
            message: コミットメッセージ
        
        Returns:
            bool: 成功したか
        """
        try:
            if message is None:
                message = f"Auto backup: {datetime.now().isoformat()}"
            
            # リポジトリのチェック
            if not os.path.exists(os.path.join(self.repo_path, ".git")):
                logger.warning("Git リポジトリが見つかりません。スキップ")
                return False
            
            # git add
            result = subprocess.run(
                ['git', 'add', 'data/'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"git add エラー: {result.stderr}")
                return False
            
            logger.info("git add 完了")
            
            # git commit
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"git commit: {result.stderr}")
                # コミットするものがない場合もあり
            
            logger.info("git commit 完了")
            
            # git push
            result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"git push エラー: {result.stderr}")
                return False
            
            logger.info("git push 完了")
            return True
        
        except subprocess.TimeoutExpired:
            logger.error("git push タイムアウト")
            return False
        except Exception as e:
            logger.error(f"Git 操作エラー: {e}")
            return False
    
    def auto_backup(self, collection, commit: bool = True) -> bool:
        """
        自動バックアップ（エクスポート＆保存＆プッシュ）
        
        Args:
            collection: Chromadb コレクション
            commit: Git プッシュするか
        
        Returns:
            bool: 成功したか
        """
        logger.info("=== 自動バックアップ開始 ===")
        
        # Step 1: エクスポート
        data = self.export_chromadb_to_json(collection)
        if not data:
            return False
        
        # Step 2: 保存
        if not self.save_backup(data):
            return False
        
        # Step 3: Git プッシュ
        if commit:
            if not self.commit_and_push(
                message=f"Auto backup: {len(data['documents'])} documents"
            ):
                logger.warning("Git プッシュに失敗しましたが、ローカル保存は成功")
                return False
        
        logger.info("=== 自動バックアップ完了 ===")
        return True
    
    def load_backup(self, filename: str = "backup.json") -> Optional[dict]:
        """
        バックアップデータを読み込む
        
        Args:
            filename: ファイル名
        
        Returns:
            dict or None: 読み込んだデータ
        """
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                logger.warning(f"ファイルが見つかりません: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"バックアップ読み込み: {filepath}")
            return data
        
        except Exception as e:
            logger.error(f"ファイル読み込みエラー: {e}")
            return None
    
    def export_purchases(self, collection) -> None:
        """
        購入データを別ファイルにエクスポート
        
        Args:
            collection: Chromadb コレクション
        """
        try:
            # 購入データを検索
            results = collection.get(
                where={"type": "purchase"}
            )
            
            purchases = {
                'timestamp': datetime.now().isoformat(),
                'total': len(results['documents']),
                'purchases': [
                    {
                        'id': results['ids'][i],
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    }
                    for i in range(len(results['documents']))
                ]
            }
            
            filepath = os.path.join(self.data_dir, "purchases.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(purchases, f, indent=2, ensure_ascii=False)
            
            logger.info(f"購入データ: {filepath} に保存")
        
        except Exception as e:
            logger.error(f"購入データ エクスポートエラー: {e}")
    
    def export_conversations(self, collection) -> None:
        """
        会話データを別ファイルにエクスポート
        
        Args:
            collection: Chromadb コレクション
        """
        try:
            # 会話データを検索
            results = collection.get(
                where={"type": "conversation"}
            )
            
            conversations = {
                'timestamp': datetime.now().isoformat(),
                'total': len(results['documents']),
                'conversations': [
                    {
                        'id': results['ids'][i],
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    }
                    for i in range(len(results['documents']))
                ]
            }
            
            filepath = os.path.join(self.data_dir, "conversations.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, indent=2, ensure_ascii=False)
            
            logger.info(f"会話データ: {filepath} に保存")
        
        except Exception as e:
            logger.error(f"会話データ エクスポートエラー: {e}")
    
    def create_weekly_summary(self, week_number: int) -> None:
        """
        週間サマリーを作成
        
        Args:
            week_number: 週番号
        """
        try:
            filename = f"weekly/week_{week_number:02d}.md"
            filepath = os.path.join(self.data_dir, filename)
            
            # ディレクトリ作成
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # サマリー内容
            content = f"""# Week {week_number:02d} Summary

## 📊 Statistics
- Generated: {datetime.now().isoformat()}

## 💬 Conversations
- Total: (自動計算)

## 💳 Purchases
- Total: (自動計算)

## 📝 Notes
- 

## 📈 Next Week Goals
-
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"週間サマリー作成: {filepath}")
        
        except Exception as e:
            logger.error(f"週間サマリー作成エラー: {e}")


# ────────────────────────────────────────
# backend_server.py に組み込む用
# ────────────────────────────────────────

"""
backend_server.py に以下を追加：

from github_manager import GitHubManager

# グローバル
github_manager = GitHubManager(".")  # リポジトリのパス

# スケジューラーに追加
async def daily_backup():
    '''毎日深夜 0:00 にバックアップ'''
    github_manager.auto_backup(collection, commit=True)

scheduler.add_job(
    daily_backup,
    'cron',
    hour=0,
    minute=0,
    name='daily_backup'
)

# エクスポート タスク
async def export_data():
    '''毎週日曜 21:00 に詳細データをエクスポート'''
    github_manager.export_purchases(collection)
    github_manager.export_conversations(collection)
    
    # 週間サマリー作成
    from datetime import date
    week_num = date.today().isocalendar()[1]
    github_manager.create_weekly_summary(week_num)

scheduler.add_job(
    export_data,
    'cron',
    day_of_week='sun',
    hour=21,
    minute=0,
    name='weekly_export'
)
"""
