"""
アナリティクスルーターの完全カバレッジ向上用テスト
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.services import text_analysis_service


class TestAnalyticsFullCoverage:
    """アナリティクスAPIの完全カバレッジ向上用テスト"""
    
    @patch("app.services.text_analysis_service.get_influencer_keywords")
    def test_get_influencer_keywords_http_exception(self, mock_get_keywords, api_test_client):
        """HTTPExceptionがそのまま再スローされるケースをテスト"""
        # HTTPExceptionを発生させる
        mock_get_keywords.side_effect = HTTPException(status_code=404, detail="Not found")
        
        # APIリクエスト
        response = api_test_client.get("/api/v1/analytics/1/keywords?limit=10")
        
        # 同じステータスコードが返されることを確認
        assert response.status_code == 404
        assert response.json()["detail"] == "Not found"
    
    @patch("app.services.text_analysis_service.get_trending_keywords")
    def test_trending_keyword_empty_result(self, mock_get_trending, api_test_client):
        """トレンドキーワードAPI - 空の結果を返すケース"""
        # 空のリストを返す
        mock_get_trending.return_value = []
        
        # APIリクエスト
        response = api_test_client.get("/api/v1/analytics/trending-keywords?days=30")
        
        # 結果を検証
        assert response.status_code == 200
        data = response.json()
        assert data["keywords"] == []
    
    @patch("app.services.text_analysis_service.get_trending_keywords")
    def test_trending_keywords_exception(self, mock_get_trending, api_test_client):
        """トレンドキーワードAPI - 例外が発生するケース"""
        # 例外を発生させる
        mock_get_trending.side_effect = Exception("Test trending error")
        
        # APIリクエスト
        response = api_test_client.get("/api/v1/analytics/trending-keywords?days=30")
        
        # 500エラーが返されることを確認
        assert response.status_code == 500
        assert "Error analyzing trending keywords" in response.json()["detail"]
    
    @patch("app.services.text_analysis_service.analyze_keywords_by_engagement")
    def test_engagement_keywords_error_handling(self, mock_analyze, api_test_client):
        """エンゲージメントキーワード分析の例外ハンドリング"""
        # 一般的な例外を発生させる
        mock_analyze.side_effect = Exception("Test error")
        
        # APIリクエスト
        response = api_test_client.get("/api/v1/analytics/keywords/engagement?engagement_type=likes")
        
        # 500エラーが返されることを確認
        assert response.status_code == 500
        assert "Error analyzing engagement keywords" in response.json()["detail"]
