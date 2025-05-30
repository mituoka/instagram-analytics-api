"""
analytics.pyのテスト
APIルーターのテストを行う
"""
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAnalyticsEndpoints:
    @patch("app.routers.analytics.text_analysis_service.get_influencer_keywords")
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

    @patch("app.routers.analytics.text_analysis_service.get_influencer_keywords")
    def test_get_influencer_keywords_exception(
        self, mock_get_keywords, api_test_client
    ):
        """インフルエンサーキーワード分析エンドポイントの一般例外処理テスト"""
        # 一般例外を発生させる（60-61行目のカバレッジ向上）
        mock_get_keywords.side_effect = Exception("一般的なエラー")

        # APIリクエスト
        response = api_test_client.get("/api/v1/analytics/1/keywords?limit=10")

        # 500エラーであることを確認
        assert response.status_code == 500
        assert "Error analyzing keywords" in response.json()["detail"]

    # """
    # # エンゲージメントキーワード分析エンドポイントの例外処理テスト
    # # エンゲージメントキーワード分析エンドポイントのValueError処理テスト
    # # 投稿数カウントでの例外処理テスト
    # """

    # @patch("app.routers.analytics.text_analysis_service.get_trending_keywords")
    # def test_get_trending_keywords_date_range_calculation(self, mock_get_keywords):
    #     """年月と月数による日付範囲計算のテスト"""
    #     # キーワードの結果をモック
    #     mock_get_keywords.return_value = [{"word": "テスト", "count": 5}]
    #
    #     # APIリクエスト - 年をまたぐ月数指定
    #     response = client.get(
    #         "/api/v1/analytics/trending-keywords?year_month=2021-11&months=5"
    #     )
    #
    #     # レスポンスの検証
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert "time_period_days" in data
    #     # 11月から5ヶ月なので、11,12,1,2,3月の日数の合計に近い値になるはず
    #     # 具体的な日数は月によって異なるが、概算で140-160日程度
    #     assert 140 < data["time_period_days"] < 165
    #
    # @patch("app.routers.analytics.text_analysis_service.get_trending_keywords")
    # def test_get_trending_keywords_all_period(self, mock_get_keywords):
    #     """期間指定なしでの全期間分析のテスト"""
    #     # キーワードの結果をモック
    #     mock_get_keywords.return_value = [{"word": "全期間", "count": 10}]
    #
    #     # APIリクエスト - パラメータなし
    #     response = client.get("/api/v1/analytics/trending-keywords")
    #
    #     # レスポンスの検証
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert "time_period_days" in data
    #     assert data["time_period_days"] is None  # 全期間なのでNullが返る
    #
    # @patch("app.routers.analytics.text_analysis_service.get_trending_keywords")
    # def test_get_trending_keywords_error_handling(self, mock_get_keywords):
    #     """トレンドキーワード取得時のエラー処理テスト"""
    #     # エラーを発生させるモック
    #     mock_get_keywords.side_effect = Exception("テスト用エラー")
    #
    #     # APIリクエスト
    #     response = client.get(
    #         "/api/v1/analytics/trending-keywords?year_month=2023-01&months=3"
    #     )
    #
    #     # エラーレスポンスの検証
    #     assert response.status_code == 500
    #     assert "Error analyzing trending keywords" in response.json()["detail"]
    #
    # def test_missing_parameter_error(self):
    #     """パラメータが不完全な場合のエラー処理テスト"""
    #     # year_monthのみでmonthsがない場合
    #     response = client.get("/api/v1/analytics/trending-keywords?year_month=2021-10")
    #     assert response.status_code == 500  # 現在の実装では500エラーが返る
    #
    #     # monthsのみでyear_monthがない場合
    #     response = client.get("/api/v1/analytics/trending-keywords?months=3")
    #     assert response.status_code == 500  # 現在の実装では500エラーが返る

    @patch("app.routers.analytics.text_analysis_service.get_influencer_keywords")
    def test_get_influencer_keywords_general_exception(self, mock_get_keywords):
        """インフルエンサーのキーワード取得で一般的な例外が発生した場合のテスト"""
        # 一般的な例外を発生させるモック
        mock_get_keywords.side_effect = Exception("一般的なエラー")

        # APIリクエスト
        response = client.get("/api/v1/analytics/1/keywords")

        # エラーレスポンスの検証
        assert response.status_code == 500
        assert "Error analyzing keywords" in response.json()["detail"]

    # @patch("app.routers.analytics.text_analysis_service.analyze_keywords_by_engagement")
    # @patch("app.routers.analytics.get_db")
    # def test_get_engagement_keywords_non_integer_count(
    #     self, mock_get_db, mock_analyze, api_test_client
    # ):
    #     """投稿数カウントが整数でない場合の処理テスト（179行目をカバー）"""
    #     # キーワード分析結果はモックで返す
    #     mock_analyze.return_value = [{"word": "テスト", "count": 5}]

    #     # カウントの部分だけを直接モック
    #     with patch(
    #         "app.routers.analytics.isinstance", return_value=False
    #     ):  # あえてisinstance()をFalseにする
    #         # APIリクエスト
    #         response = api_test_client.get(
    #             "/api/v1/analytics/keywords/engagement?engagement_type=likes&limit=10"
    #         )

    #     # レスポンスを検証
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["total_analyzed_posts"] == 100  # デフォルト値が使われる
