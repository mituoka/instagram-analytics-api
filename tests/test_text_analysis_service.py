import os
import operator
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock
from app.services.text_analysis_service import (
    extract_nouns,
    get_influencer_keywords,
    get_trending_keywords,
    analyze_keywords_by_engagement,
    get_tokenizer,
    get_cache_key,
)
from app.dependencies.cache_utils import cache
from fastapi import HTTPException
from datetime import datetime, timedelta


class TestTextAnalysisService:
    def test_extract_nouns(self):
        """名詞抽出機能のテスト"""
        # 標準的な日本語テキスト
        text = "今日は東京でインスタグラムマーケティングのセミナーに参加しました。"
        nouns = extract_nouns(text)

        # 期待される名詞が抽出されていることを確認
        expected_nouns = ["今日", "東京", "セミナー"]
        for noun in expected_nouns:
            assert noun in nouns

        # インスタグラムマーケティングは複合名詞として認識される
        assert "インスタグラム" in nouns or "インスタグラムマーケティング" in nouns

        # テストケース: 空のテキスト
        assert extract_nouns("") == []

        # テストケース: 名詞がないテキスト
        assert len(extract_nouns("あああ、いいい。")) == 0

    @patch("app.services.text_analysis_service.Tokenizer")
    @patch("app.services.text_analysis_service._tokenizer", None)  # グローバル変数を None に設定
    def test_get_tokenizer(self, mock_tokenizer_class):
        """トークナイザー取得のテスト"""
        # モックの設定
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_class.return_value = mock_tokenizer_instance

        # 初回呼び出し（トークナイザーがNoneの場合）
        tokenizer1 = get_tokenizer()

        # Tokenizerクラスが呼ばれたことを確認
        mock_tokenizer_class.assert_called_once()
        assert tokenizer1 == mock_tokenizer_instance

        # 2回目の呼び出し（既存のトークナイザーを返す）
        mock_tokenizer_class.reset_mock()
        tokenizer2 = get_tokenizer()

        # 2回目はインスタンス化せず既存のものを返す
        mock_tokenizer_class.assert_not_called()
        assert tokenizer2 == mock_tokenizer_instance

    def test_get_cache_key(self):
        """キャッシュキー生成のテスト"""
        # シンプルなキー
        key1 = get_cache_key("test")
        assert "test" in key1

        # パラメータ付きのキー
        key2 = get_cache_key("test", param1="value1", param2=123)
        key3 = get_cache_key("test", param2=123, param1="value1")  # パラメータ順序が異なる

        # 同じパラメータなら順序が違っても同じキーになるはず
        assert key2 == key3

        # 異なるパラメータなら異なるキーになるはず
        key4 = get_cache_key("test", param1="value2")
        assert key2 != key4

    @patch("app.services.text_analysis_service.extract_nouns")
    def test_get_influencer_keywords(self, mock_extract_nouns, mock_db_session):
        """インフルエンサーのキーワード抽出テスト"""
        # キャッシュをクリア
        cache.clear()

        # モックデータの設定
        mock_posts = [
            MagicMock(text="インスタグラム戦略について", post_id=1),
            MagicMock(text="フォロワー獲得のコツ", post_id=2),
            MagicMock(text="インスタグラムマーケティング", post_id=3),
        ]

        # DBクエリのモック
        mock_db_session.query().filter().all.return_value = mock_posts

        # 名詞抽出関数のモック
        mock_extract_nouns.side_effect = [
            ["インスタグラム", "戦略"],
            ["フォロワー", "獲得", "コツ"],
            ["インスタグラム", "マーケティング"],
        ]

        # テスト実行
        result = get_influencer_keywords(mock_db_session, 1, 10)

        # 結果の検証
        assert len(result) > 0
        assert any(item["word"] == "インスタグラム" and item["count"] == 2 for item in result)
        assert any(item["word"] == "戦略" and item["count"] == 1 for item in result)
        assert any(item["word"] == "フォロワー" and item["count"] == 1 for item in result)

        # キャッシュからの取得を確認
        mock_extract_nouns.reset_mock()
        cached_result = get_influencer_keywords(mock_db_session, 1, 10)
        assert cached_result == result
        # 2回目の呼び出しでは抽出関数は実行されないはず
        mock_extract_nouns.assert_not_called()

        # 存在しないインフルエンサーの場合
        mock_db_session.query().filter().all.return_value = []
        with pytest.raises(HTTPException) as excinfo:
            get_influencer_keywords(mock_db_session, 999, 10)
        assert excinfo.value.status_code == 404
        assert "Influencer with ID 999 not found" in str(excinfo.value.detail)

    @patch("app.services.text_analysis_service.extract_nouns")
    @patch("app.services.text_analysis_service.datetime")
    def test_get_trending_keywords(
        self, mock_datetime, mock_extract_nouns, mock_db_session
    ):
        """トレンドキーワード取得のテスト"""
        # キャッシュをクリア
        cache.clear()

        # 日時のモック
        now = datetime(2023, 1, 1, 12, 0)
        mock_datetime.now.return_value = now
        mock_datetime.timedelta = timedelta

        # モックデータの設定
        mock_posts = [
            MagicMock(text="最新のトレンド情報", post_id=1, post_date=now - timedelta(days=5)),
            MagicMock(
                text="インスタグラムの新機能", post_id=2, post_date=now - timedelta(days=10)
            ),
            MagicMock(text="トレンドハッシュタグ", post_id=3, post_date=now - timedelta(days=15)),
        ]

        # DBクエリのモック
        mock_db_session.query().filter().all.return_value = mock_posts

        # 名詞抽出関数のモック
        mock_extract_nouns.side_effect = [
            ["最新", "トレンド", "情報"],
            ["インスタグラム", "新機能"],
            ["トレンド", "ハッシュタグ"],
        ]

        # テスト実行
        result = get_trending_keywords(mock_db_session, limit=10, year_month="2023-01", months=1)

        # 結果の検証
        assert len(result) > 0
        assert any(item["word"] == "トレンド" and item["count"] == 2 for item in result)
        assert any(item["word"] == "インスタグラム" and item["count"] == 1 for item in result)

        # キャッシュからの取得を確認
        mock_extract_nouns.reset_mock()
        cached_result = get_trending_keywords(mock_db_session, limit=10, year_month="2023-01", months=1)
        assert cached_result == result
        # 2回目の呼び出しでは抽出関数は実行されないことの確認
        mock_extract_nouns.assert_not_called()

        # 期間内に投稿がない場合
        cache.clear()
        mock_db_session.query().filter().all.return_value = []
        empty_result = get_trending_keywords(mock_db_session, 30, 10)
        assert empty_result == []

    @patch("app.services.text_analysis_service.extract_nouns")
    def test_analyze_keywords_by_engagement(self, mock_extract_nouns, mock_db_session):
        """エンゲージメントベースのキーワード分析テスト"""
        cache.clear()

        # モックデータの設定
        mock_posts = [
            MagicMock(text="高いエンゲージメントの投稿", post_id=1, likes=1000),
            MagicMock(text="いいねがたくさんの写真", post_id=2, likes=800),
            MagicMock(text="反応が良かった企画", post_id=3, likes=750),
        ]

        # DBクエリのモック
        mock_db_session.query().order_by().limit().all.return_value = mock_posts

        # 名詞抽出関数のモック
        mock_extract_nouns.side_effect = [
            ["エンゲージメント", "投稿"],
            ["いいね", "写真"],
            ["反応", "企画"],
        ]

        # テスト実行: いいね数でのテスト
        like_result = analyze_keywords_by_engagement(mock_db_session, "likes", 10)

        # 結果の検証
        assert len(like_result) > 0
        assert any(
            item["word"] == "エンゲージメント" and item["count"] == 1 for item in like_result
        )

        # コメント数での実行
        mock_db_session.query().order_by().limit().all.return_value = mock_posts
        # 新しいモックのside_effectを設定
        mock_extract_nouns.side_effect = [
            ["エンゲージメント", "投稿"],
            ["いいね", "写真"],
            ["反応", "企画"],
        ]
        comment_result = analyze_keywords_by_engagement(mock_db_session, "comments", 10)
        assert len(comment_result) > 0
        assert any(
            item["word"] == "いいね" and item["count"] == 1 for item in comment_result
        )

        cache.clear()
        mock_extract_nouns.reset_mock()
        mock_extract_nouns.side_effect = [
            ["エンゲージメント", "投稿"],
            ["いいね", "写真"],
            ["反応", "企画"],
        ]
        first_result = analyze_keywords_by_engagement(mock_db_session, "likes", 10)
        assert mock_extract_nouns.call_count == 3

        mock_extract_nouns.reset_mock()
        cached_result = analyze_keywords_by_engagement(mock_db_session, "likes", 10)
        assert cached_result == first_result
        mock_extract_nouns.assert_not_called()

        # 投稿が取得できない場合（新しいテスト）
        cache.clear()  # テスト前にキャッシュをクリア
        mock_db_session.query().order_by().limit().all.return_value = []
        empty_result = analyze_keywords_by_engagement(mock_db_session, "likes", 10)
        assert empty_result == []

        # 不正なエンゲージメントタイプ
        with pytest.raises(ValueError) as excinfo:
            analyze_keywords_by_engagement(mock_db_session, "invalid_type", 10)
        assert "must be 'likes' or 'comments'" in str(excinfo.value)

    @patch("app.services.text_analysis_service.extract_nouns")
    def test_empty_text_processing(self, mock_extract_nouns):
        """空のテキスト処理とThreadPoolExecutorの動作テスト"""
        # モックの設定 - 呼び出されたときに空のリストを返す
        mock_extract_nouns.return_value = []

        # テスト用データ作成 - textフィールドが空のPostオブジェクト
        empty_post = MagicMock()
        empty_post.text = ""

        # テスト実行 - 各関数で空のテキスト処理があるか確認
        keywords = get_influencer_keywords(MagicMock(), 1, limit=10)
        assert isinstance(keywords, list)

        trending = get_trending_keywords(MagicMock(), year_month="2021-01", months=3, limit=10)
        assert isinstance(trending, list)

        engagement = analyze_keywords_by_engagement(
            MagicMock(), engagement_type="likes", limit=10
        )
        assert isinstance(engagement, list)

        # ThreadPoolExecutorの例外がキャッチされることを確認
        with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
            # エラーを投げるエグゼキュータをシミュレート
            mock_instance = MagicMock()
            mock_executor.return_value.__enter__.return_value = mock_instance
            mock_instance.submit.side_effect = Exception("Thread error")

            # エラーが発生しても関数が終了することを確認
            keywords = get_influencer_keywords(MagicMock(), 1, limit=10)
            assert isinstance(keywords, list)