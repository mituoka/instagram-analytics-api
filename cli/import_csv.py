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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# 注意: このインポートはsys.pathの設定後に行う必要があるため、E402警告を無視します
from app.database.connection import SessionLocal  # noqa: E402
from app.models.database_models import InfluencerPost  # noqa: E402

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(
        description="CSVファイルからインフルエンサー投稿データをインポート"
    )
    parser.add_argument("--file", required=True, help="インポートするCSVファイルのパス")
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="一度にコミットするレコード数"
    )
    return parser.parse_args()


def validate_csv_columns(reader, required_columns):
    """
    CSVファイルのヘッダーを検証
    
    Args:
        reader: CSVリーダー
        required_columns: 必須カラムのリスト
        
    Returns:
        bool: バリデーション結果（Trueなら問題なし、Falseなら問題あり）
    """
    missing_columns = [col for col in required_columns if col not in reader.fieldnames]
    if missing_columns:
        logger.error(f"CSVヘッダーに必須カラムが不足しています: {', '.join(missing_columns)}")
        return False
    return True


def create_record_from_row(row):
    """
    CSVの行からInfluencerPostレコードを作成
    
    Args:
        row: CSVの1行分のデータ
    
    Returns:
        InfluencerPost: モデルインスタンス
    """
    # 日付のパース
    post_date = datetime.strptime(row["post_date"], "%Y-%m-%d %H:%M:%S")
    
    # モデルインスタンスの作成
    return InfluencerPost(
        influencer_id=int(row["influencer_id"]),
        post_id=int(row["post_id"]),
        shortcode=row["shortcode"],
        likes=int(row["likes"]),
        comments=int(row["comments"]),
        thumbnail=row["thumbnail"],
        text=row["text"],
        post_date=post_date,
    )


def commit_records(db, records, row_count):
    """
    レコードのコミット処理
    
    Args:
        db: データベースセッション
        records: コミット対象のレコードリスト
        row_count: 処理した行数
    
    Returns:
        list: 空のリスト（コミット後にリセット）
    """
    if records:
        db.bulk_save_objects(records)
        db.commit()
        logger.info(f"{row_count}件処理しました")
    return []


def import_csv(file_path, batch_size=1000):
    """
    CSVファイルをデータベースにインポート

    Args:
        file_path: CSVファイルのパス
        batch_size: 一度にコミットするバッチサイズ
        
    Returns:
        bool: インポートの成功/失敗
    """
    # ファイルの存在チェック
    if not os.path.exists(file_path):
        logger.error(f"ファイルが見つかりません: {file_path}")
        return False

    logger.info(f"CSVファイルのインポートを開始: {file_path}")

    # 必須カラムの定義
    required_columns = [
        "influencer_id", "post_id", "shortcode", "likes",
        "comments", "thumbnail", "text", "post_date",
    ]
    
    db = SessionLocal()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # ヘッダーバリデーション
            if not validate_csv_columns(reader, required_columns):
                return False

            records = []
            row_count = 0

            # 各行を処理
            for row_count, row in enumerate(reader, 1):
                try:
                    record = create_record_from_row(row)
                    records.append(record)

                    # バッチサイズに達したらコミット
                    if row_count % batch_size == 0:
                        records = commit_records(db, records, row_count)

                except (ValueError, KeyError) as e:
                    logger.error(f"行{row_count}の処理でデータエラー: {str(e)}")
                except Exception as e:
                    logger.error(f"行{row_count}の処理で予期しないエラー: {str(e)}")
                    raise

            # 残りのレコードをコミット
            commit_records(db, records, row_count)

            logger.info(f"インポート完了: 合計{row_count}件")
            return True

    except (IOError, csv.Error) as e:
        logger.error(f"ファイル読み込み中にエラーが発生: {str(e)}")
        db.rollback()
        return False
    except Exception as e:
        logger.error(f"インポート中に予期しないエラーが発生: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
    finally:
        db.close()


def main():
    """メイン関数"""
    args = parse_args()
    success = import_csv(args.file, args.batch_size)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
