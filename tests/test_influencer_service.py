import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import func
from fastapi import HTTPException
from app.services.influencer_service import (
    get_influencer_stats,
    get_top_influencers_by_likes,
    get_top_influencers_by_comments,
)


class TestInfluencerService:
    def test_get_influencer_stats_success(self, mock_db_session):
        """インフルエンサー統計情報の取得テスト - 正常系"""
        # モックデータ設定
        mock_result = MagicMock()
        mock_result.avg_likes = 100.5
        mock_result.avg_comments = 25.3
        mock_result.total_posts = 42
        
        # クエリビルダーのモック
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        # モックチェーンの設定
        mock_db_session.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_result
        
        # テスト実行
        result = get_influencer_stats(mock_db_session, 1)
        
        # 結果検証
        assert result["influencer_id"] == 1
        assert result["avg_likes"] == 100.5
        assert result["avg_comments"] == 25.3
        assert result["total_posts"] == 42
        
        # クエリが正しく実行されたことを確認
        mock_db_session.query.assert_called_once()
        query_mock.filter.assert_called_once()
        filter_mock.first.assert_called_once()

    def test_get_influencer_stats_not_found(self, mock_db_session):
        """インフルエンサー統計情報の取得テスト - 存在しない場合"""
        # 存在しないインフルエンサーのモック
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        # first()がNoneを返すように設定
        mock_db_session.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        
        # 例外が発生することを検証
        with pytest.raises(HTTPException) as excinfo:
            get_influencer_stats(mock_db_session, 999)
        
        assert excinfo.value.status_code == 404
        assert "not found" in str(excinfo.value.detail)

    def test_get_top_influencers_by_likes(self, mock_db_session):
        """いいね数ランキングのテスト"""
        # モックデータ設定
        mock_results = [
            MagicMock(influencer_id=1, avg_likes=500.0, total_posts=20),
            MagicMock(influencer_id=2, avg_likes=300.0, total_posts=15),
            MagicMock(influencer_id=3, avg_likes=200.0, total_posts=30),
        ]
        
        # クエリビルダーのモック
        query_mock = MagicMock()
        group_mock = MagicMock()
        order_mock = MagicMock()
        limit_mock = MagicMock()
        
        # モックチェーンの設定
        mock_db_session.query.return_value = query_mock
        query_mock.group_by.return_value = group_mock
        group_mock.order_by.return_value = order_mock
        order_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = mock_results
        
        # テスト実行
        result = get_top_influencers_by_likes(mock_db_session, 3)
        
        # 結果検証
        assert len(result) == 3
        assert result[0]["influencer_id"] == 1
        assert result[0]["avg_value"] == 500.0
        assert result[0]["total_posts"] == 20

    def test_get_top_influencers_by_comments(self, mock_db_session):
        """コメント数ランキングのテスト"""
        # モックデータ設定
        mock_results = [
            MagicMock(influencer_id=3, avg_comments=50.0, total_posts=25),
            MagicMock(influencer_id=1, avg_comments=40.0, total_posts=30),
            MagicMock(influencer_id=2, avg_comments=30.0, total_posts=10),
        ]
        
        # クエリビルダーのモック
        query_mock = MagicMock()
        group_mock = MagicMock()
        order_mock = MagicMock()
        limit_mock = MagicMock()
        
        # モックチェーンの設定
        mock_db_session.query.return_value = query_mock
        query_mock.group_by.return_value = group_mock
        group_mock.order_by.return_value = order_mock
        order_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = mock_results
        
        # テスト実行
        result = get_top_influencers_by_comments(mock_db_session, 3)
        
        # 結果検証
        assert len(result) == 3
        assert result[0]["influencer_id"] == 3
        assert result[0]["avg_value"] == 50.0
        assert result[0]["total_posts"] == 25
