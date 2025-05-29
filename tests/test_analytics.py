from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError


class TestAnalyticsEndpoints:
    @patch("app.services.text_analysis_service.get_influencer_keywords")
    def test_get_influencer_keywords_success(
        self, mock_get_keywords, api_test_client, mock_keywords
    ):
        """インフルエンサーキーワード分析エンドポイントの正常系テスト"""
        # サービスメソッドをモック - KeywordCountオブジェクトをディクショナリに変換
        mock_get_keywords.return_value = [
            {"word": kw.word, "count": kw.count} for kw in mock_keywords
        ]

        # APIリクエスト
        response = api_test_client.get("/api/v1/analytics/1/keywords?limit=10")

        # レスポンスの検証
        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
        assert len(data["keywords"]) == 3
        assert data["keywords"][0]["word"] == "インスタグラム"
        assert data["keywords"][0]["count"] == 10
        assert "total_analyzed_posts" in data

    # 以下の行をカバーするための追加テスト: lines 145, 148-149, 157
    @patch("app.routers.analytics.text_analysis_service.analyze_keywords_by_engagement")
    @patch("app.routers.analytics.get_db")
    def test_get_engagement_keywords_exception_handling(
        self, mock_get_db, mock_analyze, api_test_client
    ):
        """エンゲージメントキーワード分析エンドポイントの例外処理テスト"""
        # サービス関数で例外が発生するようにモック設定
        mock_analyze.side_effect = SQLAlchemyError("Database error")

        # データベースセッションをモック
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # APIリクエスト
        response = api_test_client.get(
            "/api/v1/analytics/keywords/engagement?type=likes&limit=10"
        )

        # 500エラーであることを確認
        assert response.status_code == 500
        assert "Error analyzing engagement keywords" in response.json()["detail"]

    @patch("app.routers.analytics.text_analysis_service.analyze_keywords_by_engagement")
    @patch("app.routers.analytics.get_db")
    def test_get_engagement_keywords_value_error(
        self, mock_get_db, mock_analyze, api_test_client
    ):
        """エンゲージメントキーワード分析エンドポイントのValueError処理テスト"""
        # ValueErrorを発生させるためのテスト
        mock_analyze.side_effect = ValueError("Invalid engagement type")

        # データベースセッションをモック
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # APIリクエスト
        response = api_test_client.get(
            "/api/v1/analytics/keywords/engagement?type=invalid_type&limit=10"
        )

        # 400エラーであることを確認
        assert response.status_code == 400
        assert "Invalid engagement type" in response.json()["detail"]

    @patch("app.routers.analytics.text_analysis_service.analyze_keywords_by_engagement")
    @patch("app.routers.analytics.get_db")
    def test_get_engagement_keywords_count_exception(
        self, mock_get_db, mock_analyze, api_test_client
    ):
        """投稿数カウントでの例外処理テスト（145行目をカバー）"""
        # キーワード分析結果はモックで返す
        mock_analyze.return_value = [{"word": "テスト", "count": 5}]

        # データベースセッションをモック
        db_session = MagicMock()
        # 最初のクエリは正常に動作させる
        query_mock = MagicMock()
        db_session.query.return_value = query_mock
        # カウントクエリで例外を発生させる
        query_mock.select_from.side_effect = Exception("Count query failed")
        mock_get_db.return_value = db_session

        # APIリクエスト
        response = api_test_client.get(
            "/api/v1/analytics/keywords/engagement?type=likes&limit=10"
        )

        # レスポンスを検証（例外は内部で処理されデフォルト値が使用される）
        assert response.status_code == 200
        data = response.json()
        assert data["total_analyzed_posts"] == 100
