#!/usr/bin/env python
"""
CSVデータをPostgreSQLにインポートするCLIツール
"""
import argparse
import csv
import logging
import os
import sys
from datetime import datetime

# ルートディレクトリをPython pathに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import SessionLocal
from app.models.database_models import InfluencerPost

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(
        description='CSVファイルからインフルエンサー投稿データをインポート'
    )
    parser.add_argument(
        '--file',
        required=True,
        help='インポートするCSVファイルのパス'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='一度にコミットするレコード数'
    )
    return parser.parse_args()

def import_csv(file_path, batch_size=1000):
    """
    CSVファイルをデータベースにインポート
    
    Args:
        file_path: CSVファイルのパス
        batch_size: 一度にコミットするバッチサイズ
    """
    if not os.path.exists(file_path):
        logger.error(f"ファイルが見つかりません: {file_path}")
        return False
        
    logger.info(f"CSVファイルのインポートを開始: {file_path}")
    
    db = SessionLocal()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = []
            
            for i, row in enumerate(reader, 1):
                try:
                    # 日付のパース
                    post_date = datetime.strptime(row['post_date'], '%Y-%m-%d %H:%M:%S')
                    
                    # モデルインスタンスの作成
                    record = InfluencerPost(
                        influencer_id=int(row['influencer_id']),
                        post_id=int(row['post_id']),
                        shortcode=row['shortcode'],
                        likes=int(row['likes']),
                        comments=int(row['comments']),
                        thumbnail=row['thumbnail'],
                        text=row['text'],
                        post_date=post_date
                    )
                    records.append(record)
                    
                    # バッチサイズに達したらコミット
                    if i % batch_size == 0:
                        db.bulk_save_objects(records)
                        db.commit()
                        records = []
                        logger.info(f"{i}件処理しました")
                        
                except Exception as e:
                    logger.error(f"行{i}の処理でエラー: {str(e)}")
            
            # 残りのレコードをコミット
            if records:
                db.bulk_save_objects(records)
                db.commit()
                
            logger.info(f"インポート完了: 合計{i}件")
            return True
            
    except Exception as e:
        logger.error(f"インポート中にエラーが発生: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """メイン関数"""
    args = parse_args()
    success = import_csv(args.file, args.batch_size)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()