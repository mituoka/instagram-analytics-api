import pytest
from unittest.mock import patch, MagicMock
from app.services import influencer_service
from app.models.schemas import InfluencerRanking


@pytest.fixture
def mock_ranking_data():
    return [
        {"influencer_id": 1, "avg_value": 1500.5, "total_posts": 20},
        {"influencer_id": 2, "avg_value": 1200.0, "total_posts": 15},
        {"influencer_id": 3, "avg_value": 800.75, "total_posts": 30},
    ]


@pytest.fixture
def mock_stats_data():
    return {
        "influencer_id": 1,
        "avg_likes": 1500.5,
        "avg_comments": 120.25,
        "total_posts": 20,
    }


class TestInfluencerEndpoints:
    @patch("app.routers.influencer.influencer_service.get_influencer_stats")
    def test_get_influencer_stats_success(self, mock_stats, api_test_client, mock_stats_data):
        """インフルエンサー統計情報取得エンドポイントの正常系テスト"""
        # モックの設定
        mock_stats.return_value = mock_stats_data
        
        # APIリクエスト
        response = api_test_client.get("/api/v1/influencers/1/stats")
        
        # レスポンスの検証
        assert response.status_code == 200
        data = response.json()
        assert data["influencer_id"] == 1
        assert data["avg_likes"] == 1500.5
        assert data["avg_comments"] == 120.25
        assert data["total_posts"] == 20
        
        # モックが正しく呼び出されたことを確認
        mock_stats.assert_called_once()

    @patch("app.routers.influencer.influencer_service.get_influencer_stats")
    def test_get_influencer_stats_not_found(self, mock_stats, api_test_client):
        """インフルエンサー統計情報取得エンドポイントの存在しないIDテスト"""
        # モックが例外を投げるように設定
        from fastapi import HTTPException
        mock_stats.side_effect = HTTPException(status_code=404, detail="Influencer not found")
        
        # APIリクエスト
        response = api_test_client.get("/api/v1/influencers/999/stats")
        
        # 404エラーが返ることを確認
        assert response.status_code == 404

    @patch("app.routers.influencer.influencer_service.get_top_influencers_by_likes")
    def test_get_likes_ranking(self, mock_likes_ranking, api_test_client, mock_ranking_data):
        """いいね数ランキング取得エンドポイントのテスト"""
        # モックの設定
        mock_likes_ranking.return_value = mock_ranking_data
        
        # APIリクエスト
        response = api_test_client.get("/api/v1/influencers/ranking/likes?limit=3")
        
        # レスポンスの検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["influencer_id"] == 1
        assert data[0]["avg_value"] == 1500.5
        assert data[0]["total_posts"] == 20
        
        # モックが正しく呼び出されたことを確認
        mock_likes_ranking.assert_called_once()

    @patch("app.routers.influencer.influencer_service.get_top_influencers_by_comments")
    def test_get_comments_ranking(self, mock_comments_ranking, api_test_client, mock_ranking_data):
        """コメント数ランキング取得エンドポイントのテスト"""
        # モックの設定
        mock_comments_ranking.return_value = mock_ranking_data
        
        # APIリクエスト
        response = api_test_client.get("/api/v1/influencers/ranking/comments?limit=3")
        
        # レスポンスの検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["influencer_id"] == 1
        assert data[0]["avg_value"] == 1500.5
        assert data[0]["total_posts"] == 20
        
        # モックが正しく呼び出されたことを確認
        mock_comments_ranking.assert_called_once()
