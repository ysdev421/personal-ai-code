"""
GitHub マネージャー（2 リポジトリ対応）
- personal-ai-code: ソースコード（Public）
- personal-ai-data: 個人データ（Private）
"""

import os
import json
import subprocess
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DualRepositoryManager:
    """2 つのリポジトリを管理"""
    
    def __init__(self, 
                 code_repo_path: str = "../personal-ai-code",
                 data_repo_path: str = "../personal-ai-data"):
        """
        初期化
        
        Args:
            code_repo_path: ソースコードリポジトリのパス
            data_repo_path: データバックアップリポジトリのパス
        """
        self.code_repo_path = code_repo_path
        self.data_repo_path = data_repo_path
        self.data_dir = os.path.join(data_repo_path, "data")
        
        # data/ ディレクトリがなければ作成
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"ディレクトリ作成: {self.data_dir}")
    
    # ────────────────────────────────────────
    # 【リポジトリ 1】ソースコード管理
    # ────────────────────────────────────────
    
    def push_source_code(self, message: Optional[str] = None) -> bool:
        """
        ソースコードを GitHub に push（必要に応じて）
        
        Args:
            message: コミットメッセージ
        
        Returns:
            bool: 成功したか
        """
        try:
            if message is None:
                message = f"Update: {datetime.now().isoformat()}"
            
            # リポジトリのチェック
            if not os.path.exists(os.path.join(self.code_repo_path, ".git")):
                logger.warning("ソースコードリポジトリが見つかりません")
                return False
            
            # git add
            subprocess.run(
                ['git', 'add', '.'],
                cwd=self.code_repo_path,
                capture_output=True
            )
            
            # git commit
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.code_repo_path,
                capture_output=True,
                text=True
            )
            
            # git push
            result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=self.code_repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"ソースコード push: {message}")
                return True
            else:
                logger.warning(f"ソースコード push 失敗: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"ソースコード push エラー: {e}")
            return False
    
    # ────────────────────────────────────────
    # 【リポジトリ 2】個人データバックアップ
    # ────────────────────────────────────────
    
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
    
    def save_backup_data(self, data: dict, filename: str = "backup.json") -> bool:
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
    
    def push_backup_data(self, message: Optional[str] = None) -> bool:
        """
        個人データを GitHub に push
        
        Args:
            message: コミットメッセージ
        
        Returns:
            bool: 成功したか
        """
        try:
            if message is None:
                message = f"Auto backup: {datetime.now().isoformat()}"
            
            # リポジトリのチェック
            if not os.path.exists(os.path.join(self.data_repo_path, ".git")):
                logger.warning("データリポジトリが見つかりません")
                return False
            
            # git add data/ のみ
            subprocess.run(
                ['git', 'add', 'data/'],
                cwd=self.data_repo_path,
                capture_output=True
            )
            
            # git commit
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.data_repo_path,
                capture_output=True,
                text=True
            )
            
            # git push
            result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=self.data_repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"データ push: {message}")
                return True
            else:
                logger.warning(f"データ push 失敗（無視）: {result.stderr}")
                # ネットワークエラーなどでも続行
                return False
        
        except subprocess.TimeoutExpired:
            logger.warning("データ push タイムアウト（無視）")
            return False
        except Exception as e:
            logger.error(f"データ push エラー（無視）: {e}")
            return False
    
    async def auto_backup(self, collection) -> bool:
        """
        自動バックアップ（エクスポート＆保存＆プッシュ）
        
        Args:
            collection: Chromadb コレクション
        
        Returns:
            bool: 成功したか
        """
        logger.info("=== 自動バックアップ開始 ===")
        
        # Step 1: エクスポート
        data = self.export_chromadb_to_json(collection)
        if not data:
            return False
        
        # Step 2: 保存
        if not self.save_backup_data(data):
            return False
        
        # Step 3: GitHub に push
        self.push_backup_data(
            message=f"Auto backup: {len(data['documents'])} documents"
        )
        
        logger.info("=== 自動バックアップ完了 ===")
        return True
    
    def export_purchases(self, collection) -> None:
        """購入データを別ファイルにエクスポート"""
        try:
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
        """会話データを別ファイルにエクスポート"""
        try:
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
        """週間サマリーを作成"""
        try:
            weekly_dir = os.path.join(self.data_dir, "weekly")
            os.makedirs(weekly_dir, exist_ok=True)
            
            filename = f"week_{week_number:02d}.md"
            filepath = os.path.join(weekly_dir, filename)
            
            content = f"""# Week {week_number:02d} Summary

Generated: {datetime.now().isoformat()}

## 📊 Statistics

## 💬 Conversations

## 💳 Purchases

## 📝 Notes

## 📈 Next Week Goals
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"週間サマリー作成: {filepath}")
        
        except Exception as e:
            logger.error(f"週間サマリー作成エラー: {e}")
    
    def push_all(self, collection) -> None:
        """
        全てを push（手動で呼ぶ用）
        
        Args:
            collection: Chromadb コレクション
        """
        logger.info("全リポジトリに push 開始...")
        
        # データをエクスポート＆保存
        self.export_purchases(collection)
        self.export_conversations(collection)
        
        # 週間サマリー
        from datetime import date
        week_num = date.today().isocalendar()[1]
        self.create_weekly_summary(week_num)
        
        # データリポジトリに push
        self.push_backup_data(f"Weekly update: {datetime.now()}")
        
        logger.info("全 push 完了")
