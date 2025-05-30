"""
トレンドキーワード分析機能の単体テスト
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi import HTTPException

from app.services.text_analysis_service import get_trending_keywords
from app.dependencies.cache_utils import cache


class TestTrendingKeywords:
    """トレンドキーワード分析の単体テスト"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """各テスト実行前の共通設定"""
        # キャッシュをクリア
        cache.clear()

    @patch("app.services.text_analysis_service.extract_nouns")
    def test_trending_keywords_by_year_month(self, mock_extract_nouns):
        """年月と期間指定でのトレンドキーワード分析のテスト"""
        # モックデータの設定
        post1 = MagicMock(
            id=1,
            post_id=1001,
            influencer_id=1,
            text="2023年1月のトレンド情報",
            post_date=datetime(2023, 1, 15),
        )
        post2 = MagicMock(
            id=2,
            post_id=1002,
            influencer_id=2,
            text="2023年2月の新機能情報",
            post_date=datetime(2023, 2, 10),
        )
        post3 = MagicMock(
            id=3,
            post_id=1003,
            influencer_id=3,
            text="2023年3月のマーケティングトレンド",
            post_date=datetime(2023, 3, 5),
        )

        # DBのモック設定
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [post1, post2, post3]

        # 投稿数カウントのモック
        mock_filter.count.return_value = 3
        mock_query.count.return_value = 3

        # 名詞抽出関数のモック
        mock_extract_nouns.side_effect = [
            ["トレンド", "情報"],
            ["新機能", "情報"],
            ["マーケティング", "トレンド"],
        ]

        # テスト実行: 2023年1月から3ヶ月間のデータ分析
        result = get_trending_keywords(
            mock_db, year_month="2023-01", months=3, limit=10
        )

        # 結果の検証
        assert len(result) > 0
        # トレンドは2回出現
        assert any(item["word"] == "トレンド" and item["count"] == 2 for item in result)
        # 情報は2回出現
        assert any(item["word"] == "情報" and item["count"] == 2 for item in result)

    @patch("app.services.text_analysis_service.extract_nouns")
    def test_trending_keywords_with_invalid_year_month_format(self, mock_extract_nouns):
        """無効な年月形式でのエラー処理テスト"""
        mock_db = MagicMock()

        # 無効な年月形式でテスト実行
        with pytest.raises(HTTPException) as excinfo:
            get_trending_keywords(
                mock_db, year_month="invalid-format", months=3, limit=10
            )

        # エラーメッセージの検証
        assert excinfo.value.status_code == 400
        assert "無効な年月形式" in str(excinfo.value.detail)

    def test_trending_keywords_empty_results(self):
        """データがない場合のテスト"""
        # DBのモック設定 - 空のリストを返す
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []
        mock_filter.count.return_value = 0
        mock_query.count.return_value = 0

        # テスト実行 (パラメータなしでも動作するようになった)
        result = get_trending_keywords(mock_db, limit=10)

        # 結果の検証
        assert result == []

    @patch("app.services.text_analysis_service.extract_nouns")
    def test_trending_keywords_cache_functionality(self, mock_extract_nouns):
        """キャッシュ機能のテスト"""
        # モックデータの設定
        post = MagicMock(
            id=1,
            post_id=1001,
            influencer_id=1,
            text="キャッシュテスト用テキスト",
            post_date=datetime.now(),
        )

        # DBのモック設定
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [post]
        mock_filter.count.return_value = 1
        mock_query.count.return_value = 1

        # 名詞抽出関数のモック
        mock_extract_nouns.return_value = ["キャッシュ", "テスト"]

        # 1回目の実行（キャッシュに保存される）
        first_result = get_trending_keywords(
            mock_db, year_month="2023-01", months=1, limit=10
        )

        # 抽出関数が呼ばれたことを確認
        assert mock_extract_nouns.call_count == 1

        # 2回目の実行（キャッシュから読み込まれる）
        mock_extract_nouns.reset_mock()
        second_result = get_trending_keywords(
            mock_db, year_month="2023-01", months=1, limit=10
        )

        # 結果が同じで、抽出関数が呼ばれていないことを確認
        assert second_result == first_result
        mock_extract_nouns.assert_not_called()
