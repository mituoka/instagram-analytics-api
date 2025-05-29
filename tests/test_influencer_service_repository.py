"""
インフルエンサーサービスリポジトリのユニットテスト
実装されたリポジトリパターンを使用するサービス層のテスト
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.services import influencer_service_repository


class TestInfluencerServiceRepository:
    @patch("app.services.influencer_service_repository.InfluencerPostRepository")
    def test_get_influencer_stats_success(self, mock_repository):
        """インフルエンサー統計情報取得の正常系テスト"""
        # モックセッションとモックリポジトリの設定
        mock_db = MagicMock(spec=Session)
        mock_repo_instance = MagicMock()
        mock_repository.return_value = mock_repo_instance
        
        # リポジトリの戻り値をモック
        mock_stats = MagicMock()
        mock_stats.avg_likes = 1500.5
        mock_stats.avg_comments = 120.25
        mock_stats.total_posts = 20
        mock_repo_instance.get_influencer_stats.return_value = mock_stats
        
        # 関数実行
        result = influencer_service_repository.get_influencer_stats(mock_db, 1)
        
        # 検証
        mock_repository.assert_called_once_with(mock_db)
        mock_repo_instance.get_influencer_stats.assert_called_once_with(1)
        assert result["influencer_id"] == 1
        assert result["avg_likes"] == 1500.5
        assert result["avg_comments"] == 120.25
        assert result["total_posts"] == 20

    @patch("app.services.influencer_service_repository.InfluencerPostRepository")
    def test_get_influencer_stats_not_found(self, mock_repository):
        """インフルエンサー統計情報取得の存在しないIDテスト"""
        # モックセッションとモックリポジトリの設定
        mock_db = MagicMock(spec=Session)
        mock_repo_instance = MagicMock()
        mock_repository.return_value = mock_repo_instance
        
        # 存在しないIDの場合はNoneを返す
        mock_repo_instance.get_influencer_stats.return_value = None
        
        # 例外が発生することを確認
        with pytest.raises(HTTPException) as excinfo:
            influencer_service_repository.get_influencer_stats(mock_db, 999)
        
        # エラー内容の検証
        assert excinfo.value.status_code == 404
        assert "Influencer with ID 999 not found" in str(excinfo.value.detail)

    @patch("app.services.influencer_service_repository.InfluencerPostRepository")
    def test_get_top_influencers_by_likes(self, mock_repository):
        """いいね数ランキング取得のテスト"""
        # モックセッションとモックリポジトリの設定
        mock_db = MagicMock(spec=Session)
        mock_repo_instance = MagicMock()
        mock_repository.return_value = mock_repo_instance
        
        # リポジトリの戻り値をモック
        mock_ranking = [
            MagicMock(influencer_id=1, avg_likes=1500.5, total_posts=20),
            MagicMock(influencer_id=2, avg_likes=1200.0, total_posts=15),
            MagicMock(influencer_id=3, avg_likes=800.75, total_posts=30),
        ]
        mock_repo_instance.get_top_by_likes.return_value = mock_ranking
        
        # 関数実行
        result = influencer_service_repository.get_top_influencers_by_likes(mock_db, 3)
        
        # 検証
        mock_repository.assert_called_once_with(mock_db)
        mock_repo_instance.get_top_by_likes.assert_called_once_with(3)
        assert len(result) == 3
        assert result[0]["influencer_id"] == 1
        assert result[0]["avg_value"] == 1500.5
        assert result[0]["total_posts"] == 20

    @patch("app.services.influencer_service_repository.InfluencerPostRepository")
    def test_get_top_influencers_by_comments(self, mock_repository):
        """コメント数ランキング取得のテスト"""
        # モックセッションとモックリポジトリの設定
        mock_db = MagicMock(spec=Session)
        mock_repo_instance = MagicMock()
        mock_repository.return_value = mock_repo_instance
        
        # リポジトリの戻り値をモック
        mock_ranking = [
            MagicMock(influencer_id=1, avg_comments=120.5, total_posts=20),
            MagicMock(influencer_id=2, avg_comments=100.0, total_posts=15),
            MagicMock(influencer_id=3, avg_comments=80.75, total_posts=30),
        ]
        mock_repo_instance.get_top_by_comments.return_value = mock_ranking
        
        # 関数実行
        result = influencer_service_repository.get_top_influencers_by_comments(mock_db, 3)
        
        # 検証
        mock_repository.assert_called_once_with(mock_db)
        mock_repo_instance.get_top_by_comments.assert_called_once_with(3)
        assert len(result) == 3
        assert result[0]["influencer_id"] == 1
        assert result[0]["avg_value"] == 120.5
        assert result[0]["total_posts"] == 20
