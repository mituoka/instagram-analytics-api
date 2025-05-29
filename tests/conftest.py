"""
APIテスト用のフィクスチャ設定ファイル
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db
from app.models.schemas import KeywordCount


@pytest.fixture
def mock_db_session():
    """DB依存性を完全にモックするためのフィクスチャ"""
    mock_db = MagicMock()

    # 一般的なクエリチェーンのモック
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.scalar.return_value = 15

    return mock_db


@pytest.fixture
def api_test_client(mock_db_session):
    """APIテスト専用のTestClientフィクスチャ"""

    # DB依存性のオーバーライド
    def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # テスト後に依存性のオーバーライドをクリア
    app.dependency_overrides.clear()


@pytest.fixture
def mock_keywords():
    """テスト用キーワードデータ"""
    return [
        KeywordCount(word="インスタグラム", count=10),
        KeywordCount(word="フォロワー", count=8),
        KeywordCount(word="マーケティング", count=5),
    ]
