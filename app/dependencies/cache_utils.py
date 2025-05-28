"""
キャッシュ機能を提供するユーティリティモジュール
API応答のパフォーマンスを向上させるためのシンプルなインメモリキャッシュを実装
"""

import time
from typing import Any, Dict, Optional, Tuple


class SimpleCache:
    """
    シンプルなインメモリキャッシュクラス
    TTL（Time To Live）でキャッシュの有効期限を設定可能
    """

    def __init__(self):
        """キャッシュを初期化"""
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        指定したキーでキャッシュから値を取得

        Args:
            key: キャッシュのキー

        Returns:
            Any または None: キャッシュされた値（有効期限切れまたは存在しない場合はNone）
        """
        if key not in self._cache:
            return None

        timestamp, value = self._cache[key]
        if timestamp < time.time():
            self._cache.pop(key)
            return None

        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """
        指定したキーで値をキャッシュに保存

        Args:
            key: キャッシュのキー
            value: キャッシュする値
            ttl_seconds: キャッシュの有効期間（秒）、デフォルトは300秒（5分）
        """
        expiry = time.time() + ttl_seconds
        self._cache[key] = (expiry, value)

    def invalidate(self, key: str) -> None:
        """
        指定したキーのキャッシュを無効化

        Args:
            key: 無効化するキャッシュのキー
        """
        if key in self._cache:
            self._cache.pop(key)

    def clear(self) -> None:
        """キャッシュをすべてクリア"""
        self._cache.clear()


# グローバルキャッシュインスタンス
cache = SimpleCache()
