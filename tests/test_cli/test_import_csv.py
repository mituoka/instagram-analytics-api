"""
cli/import_csv.py のテスト
"""
import csv
import os
import pytest
from unittest import mock
from datetime import datetime

from cli.import_csv import (
    parse_args,
    validate_csv_columns,
    create_record_from_row,
    commit_records,
    process_csv_row,
    process_csv_file,
    import_csv,
    main,
)
from app.models.database_models import InfluencerPost


class TestParseArgs:
    def test_parse_args_default(self):
        """デフォルト値でのコマンドライン引数パースのテスト"""
        with mock.patch('sys.argv', ['import_csv.py', '--file', 'test.csv']):
            args = parse_args()
            assert args.file == 'test.csv'
            assert args.batch_size == 1000  # デフォルト値

    def test_parse_args_custom_batch_size(self):
        """カスタムバッチサイズでのコマンドライン引数パースのテスト"""
        with mock.patch('sys.argv', ['import_csv.py', '--file', 'test.csv', '--batch-size', '500']):
            args = parse_args()
            assert args.file == 'test.csv'
            assert args.batch_size == 500


class TestValidateCsvColumns:
    def test_valid_columns(self):
        """有効なカラムでCSV検証が成功するテスト"""
        # mockのDictReaderを作成
        mock_reader = mock.MagicMock()
        mock_reader.fieldnames = ['influencer_id', 'post_id', 'shortcode', 'likes', 'comments', 'thumbnail', 'text', 'post_date']
        required_columns = ['influencer_id', 'post_id', 'shortcode', 'likes', 'comments', 'thumbnail', 'text', 'post_date']

        assert validate_csv_columns(mock_reader, required_columns) is True

    def test_missing_columns(self):
        """不足カラムがある場合にCSV検証が失敗するテスト"""
        mock_reader = mock.MagicMock()
        mock_reader.fieldnames = ['influencer_id', 'post_id', 'shortcode', 'likes']  # 一部のカラムが不足
        required_columns = ['influencer_id', 'post_id', 'shortcode', 'likes', 'comments', 'thumbnail', 'text', 'post_date']

        assert validate_csv_columns(mock_reader, required_columns) is False


class TestCreateRecordFromRow:
    def test_create_record_success(self):
        """正常な行データからレコード作成が成功するテスト"""
        row = {
            'influencer_id': '1',
            'post_id': '123',
            'shortcode': 'abc123',
            'likes': '100',
            'comments': '50',
            'thumbnail': 'https://example.com/thumb.jpg',
            'text': 'Test post text',
            'post_date': '2023-01-01 12:00:00'
        }

        record = create_record_from_row(row)
        
        assert isinstance(record, InfluencerPost)
        assert record.influencer_id == 1
        assert record.post_id == 123
        assert record.shortcode == 'abc123'
        assert record.likes == 100
        assert record.comments == 50
        assert record.thumbnail == 'https://example.com/thumb.jpg'
        assert record.text == 'Test post text'
        assert record.post_date == datetime(2023, 1, 1, 12, 0, 0)
    
    def test_create_record_invalid_data(self):
        """不正な行データからレコード作成が例外を発生させるテスト"""
        row = {
            'influencer_id': 'not-a-number',  # 数値ではない
            'post_id': '123',
            'shortcode': 'abc123',
            'likes': '100',
            'comments': '50',
            'thumbnail': 'https://example.com/thumb.jpg',
            'text': 'Test post text',
            'post_date': '2023-01-01 12:00:00'
        }

        with pytest.raises(ValueError):
            create_record_from_row(row)
    
    def test_create_record_invalid_date(self):
        """不正な日付フォーマットでレコード作成が例外を発生させるテスト"""
        row = {
            'influencer_id': '1',
            'post_id': '123',
            'shortcode': 'abc123',
            'likes': '100',
            'comments': '50',
            'thumbnail': 'https://example.com/thumb.jpg',
            'text': 'Test post text',
            'post_date': 'invalid-date'  # 不正な日付フォーマット
        }

        with pytest.raises(ValueError):
            create_record_from_row(row)


class TestCommitRecords:
    def test_commit_with_records(self):
        """レコードがある場合のコミット処理テスト"""
        mock_db = mock.MagicMock()
        mock_records = [mock.MagicMock(), mock.MagicMock()]
        
        result = commit_records(mock_db, mock_records, 100)
        
        # データベースのbulk_save_objectsとcommitが呼ばれたことを確認
        mock_db.bulk_save_objects.assert_called_once_with(mock_records)
        mock_db.commit.assert_called_once()
        # 結果が空リストであることを確認
        assert result == []
    
    def test_commit_with_empty_records(self):
        """レコードがない場合のコミット処理テスト"""
        mock_db = mock.MagicMock()
        mock_records = []
        
        result = commit_records(mock_db, mock_records, 0)
        
        # データベース操作が呼ばれていないことを確認
        mock_db.bulk_save_objects.assert_not_called()
        mock_db.commit.assert_not_called()
        # 空リストが返されることを確認
        assert result == []


class TestProcessCsvRow:
    def test_process_row_normal(self):
        """通常の行処理のテスト"""
        mock_db = mock.MagicMock()
        mock_records = []
        row = {
            'influencer_id': '1',
            'post_id': '123',
            'shortcode': 'abc123',
            'likes': '100',
            'comments': '50',
            'thumbnail': 'https://example.com/thumb.jpg',
            'text': 'Test post text',
            'post_date': '2023-01-01 12:00:00'
        }
        
        # バッチサイズに満たない行数の処理
        result = process_csv_row(mock_db, row, mock_records, 10, 5)
        
        # レコードが追加されていることを確認
        assert len(result) == 1
        assert isinstance(result[0], InfluencerPost)
    
    def test_process_row_batch_commit(self):
        """バッチコミットが発生するケースのテスト"""
        mock_db = mock.MagicMock()
        mock_records = [mock.MagicMock()]  # 既存のレコード
        row = {
            'influencer_id': '1',
            'post_id': '123',
            'shortcode': 'abc123',
            'likes': '100',
            'comments': '50',
            'thumbnail': 'https://example.com/thumb.jpg',
            'text': 'Test post text',
            'post_date': '2023-01-01 12:00:00'
        }
        
        # バッチサイズに達した行数の処理
        with mock.patch('cli.import_csv.commit_records', return_value=[]) as mock_commit:
            result = process_csv_row(mock_db, row, mock_records, 10, 10)
            
            # commit_recordsが呼ばれたことを確認
            mock_commit.assert_called_once()
            # 空リストが返されることを確認
            assert result == []
    
    def test_process_row_value_error(self):
        """行データ処理時の値エラーハンドリングテスト"""
        mock_db = mock.MagicMock()
        mock_records = []
        row = {
            'influencer_id': 'invalid',  # 不正な値
            'post_id': '123',
            'shortcode': 'abc123',
            'likes': '100',
            'comments': '50',
            'thumbnail': 'https://example.com/thumb.jpg',
            'text': 'Test post text',
            'post_date': '2023-01-01 12:00:00'
        }
        
        # エラーは処理され、元のレコードリストが返されることを確認
        result = process_csv_row(mock_db, row, mock_records, 10, 5)
        assert result == mock_records


@pytest.fixture
def mock_csv_file():
    """一時的なモックCSVファイルを作成するフィクスチャ"""
    file_path = 'test_data.csv'
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'influencer_id', 'post_id', 'shortcode', 'likes', 
            'comments', 'thumbnail', 'text', 'post_date'
        ])
        writer.writeheader()
        writer.writerow({
            'influencer_id': '1',
            'post_id': '123',
            'shortcode': 'abc123',
            'likes': '100',
            'comments': '50',
            'thumbnail': 'https://example.com/thumb.jpg',
            'text': 'Test post text',
            'post_date': '2023-01-01 12:00:00'
        })
    
    yield file_path
    
    # テスト後にファイルを削除
    if os.path.exists(file_path):
        os.remove(file_path)


class TestProcessCsvFile:
    def test_process_file_success(self, mock_csv_file):
        """CSVファイル処理の成功テスト"""
        mock_db = mock.MagicMock()
        
        with mock.patch('cli.import_csv.validate_csv_columns', return_value=True):
            with mock.patch('cli.import_csv.process_csv_row') as mock_process_row:
                # process_csv_rowが呼ばれるたびに空リストを返す設定
                mock_process_row.return_value = []
                
                result = process_csv_file(mock_csv_file, mock_db, 10)
                
                # 処理が成功し、True が返されることを確認
                assert result is True
                # process_csv_rowが呼ばれたことを確認
                assert mock_process_row.called
    
    def test_process_file_validation_failure(self, mock_csv_file):
        """CSVバリデーション失敗のテスト"""
        mock_db = mock.MagicMock()
        
        with mock.patch('cli.import_csv.validate_csv_columns', return_value=False):
            result = process_csv_file(mock_csv_file, mock_db, 10)
            
            # バリデーション失敗でFalseが返されることを確認
            assert result is False


class TestImportCsv:
    def test_import_nonexistent_file(self):
        """存在しないファイルのインポート失敗テスト"""
        result = import_csv('nonexistent_file.csv')
        assert result is False
    
    def test_import_success(self, mock_csv_file):
        """CSVインポート成功のテスト"""
        with mock.patch('cli.import_csv.SessionLocal') as mock_session:
            mock_db = mock.MagicMock()
            mock_session.return_value = mock_db
            
            with mock.patch('cli.import_csv.process_csv_file', return_value=True) as mock_process:
                result = import_csv(mock_csv_file)
                
                # インポートが成功し、True が返されることを確認
                assert result is True
                # process_csv_fileが呼ばれたことを確認
                mock_process.assert_called_once_with(mock_csv_file, mock_db, 1000)
                # DBセッションがクローズされたことを確認
                mock_db.close.assert_called_once()
    
    def test_import_io_error(self, mock_csv_file):
        """IOエラー発生時の処理テスト"""
        with mock.patch('cli.import_csv.SessionLocal') as mock_session:
            mock_db = mock.MagicMock()
            mock_session.return_value = mock_db
            
            with mock.patch('cli.import_csv.process_csv_file', side_effect=IOError("IO Error")) as mock_process:
                result = import_csv(mock_csv_file)
                
                # エラーが処理され、False が返されることを確認
                assert result is False
                # DBロールバックが呼ばれたことを確認
                mock_db.rollback.assert_called_once()
                # DBセッションがクローズされたことを確認
                mock_db.close.assert_called_once()


class TestMain:
    def test_main_success(self):
        """メイン関数の成功パターンテスト"""
        with mock.patch('cli.import_csv.parse_args') as mock_parse_args:
            mock_args = mock.MagicMock()
            mock_args.file = 'test.csv'
            mock_args.batch_size = 1000
            mock_parse_args.return_value = mock_args
            
            with mock.patch('cli.import_csv.import_csv', return_value=True) as mock_import:
                with mock.patch('sys.exit') as mock_exit:
                    main()
                    
                    # import_csvが正しい引数で呼ばれたことを確認
                    mock_import.assert_called_once_with('test.csv', 1000)
                    # 成功時に終了コード0で終了することを確認
                    mock_exit.assert_called_once_with(0)
    
    def test_main_failure(self):
        """メイン関数の失敗パターンテスト"""
        with mock.patch('cli.import_csv.parse_args') as mock_parse_args:
            mock_args = mock.MagicMock()
            mock_args.file = 'test.csv'
            mock_args.batch_size = 1000
            mock_parse_args.return_value = mock_args
            
            with mock.patch('cli.import_csv.import_csv', return_value=False) as mock_import:
                with mock.patch('sys.exit') as mock_exit:
                    main()
                    
                    # 失敗時に終了コード1で終了することを確認
                    mock_exit.assert_called_once_with(1)
