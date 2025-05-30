"""
テキスト分析機能を提供するサービスレイヤー
日本語の形態素解析、名詞抽出、キーワードカウントなどの機能を提供します
パフォーマンス最適化（キャッシュ、並行処理）を実装
"""

import os
from app.dependencies.cache_utils import get_cache_key
from janome.tokenizer import Tokenizer
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from fastapi import HTTPException
import re
import hashlib
import json
import concurrent.futures
from datetime import datetime

from app.models.database_models import InfluencerPost
from app.dependencies.cache_utils import cache

# Janomeトークナイザーのシングルトンインスタンス（メモリ効率化のため）
_tokenizer = None


def get_tokenizer():
    """
    Janomeトークナイザーのシングルトンインスタンスを取得

    Returns:
        Tokenizer: Janome形態素解析器のインスタンス
    """
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = Tokenizer()
    return _tokenizer


def extract_nouns(content: str) -> List[str]:
    """
    テキストから名詞を抽出する関数

    Args:
        content: 分析対象のテキスト

    Returns:
        List[str]: 抽出された名詞のリスト
    """
    if not content:
        return []

    # トークナイザーを取得
    tokenizer = get_tokenizer()

    # 前処理: 不要な文字を削除してトークン化負荷を軽減
    # URLやハッシュタグ、メンション等を事前にフィルタリング
    content = re.sub(r"https?://\S+|www\.\S+", "", content)

    # テキストをトークン化し、名詞のみを取得（ジェネレータ式で効率化）

    nouns = [
        token.surface
        for token in tokenizer.tokenize(content)
        if token.part_of_speech.split(",")[0] == "名詞"
        and len(token.surface) > 1  # 1文字の名詞は除外
        and not re.match(
            r"^[0-9０-９]+$|^[!-/:-@[-`{-~]+$", token.surface
        )  # 数字や記号のみの場合も除外
        and not re.match(
            r"^[0-9０-９]+$|^[!-/:-@[-`{-~]+$", token.surface
        )  # 数字や記号のみの場合も除外
    ]

    return nouns


def get_influencer_keywords(
    db: Session, influencer_id: int, limit: int = 10
) -> List[Dict]:
    """
    指定されたインフルエンサーの投稿から頻出キーワード（名詞）を抽出
    結果をキャッシュして高速化（30分有効）

    Args:
        db: データベースセッション
        influencer_id: インフルエンサーID
        limit: 返すキーワードの最大数

    Returns:
        List[Dict]: キーワードと出現回数のリスト

    Raises:
        HTTPException: インフルエンサーIDに該当する投稿が見つからない場合
    """
    # キャッシュキーを作成
    cache_key = get_cache_key(
        "influencer_keywords", influencer_id=influencer_id, limit=limit
    )

    # キャッシュをチェック
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    # インフルエンサーの最新データを確認するためのクエリ（キャッシュ制御用）
    _ = (
        db.query(func.max(InfluencerPost.updated_at))
        .filter(InfluencerPost.influencer_id == influencer_id)
        .scalar()
    )

    # インフルエンサーの投稿を取得
    posts = (
        db.query(InfluencerPost)
        .filter(InfluencerPost.influencer_id == influencer_id)
        .all()
    )

    if not posts:
        raise HTTPException(
            status_code=404, detail=f"Influencer with ID {influencer_id} not found"
        )

    # 名詞抽出（並行処理）
    all_nouns = []

    def process_text(text):
        if text:
            return extract_nouns(text)
        return [] # pragma: no cover

    max_workers = min(max(os.cpu_count() or 4, 2), 10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_text = {
            executor.submit(process_text, post.text): post
            for post in posts
            if post.text
        }

        for future in concurrent.futures.as_completed(future_to_text):
            all_nouns.extend(future.result())

    # カウント、ソート、整形
    counter = Counter(all_nouns)
    top_keywords = counter.most_common(limit)
    result = [{"word": word, "count": count} for word, count in top_keywords]

    # キャッシュ保存（30分）
    cache.set(cache_key, result, ttl_seconds=1800)

    return result


# def get_cache_key(prefix: str, **kwargs) -> str:
#     """
#     キャッシュキーを生成する関数
#     データ量に応じてキャッシュの有効期間を調整可能

#     Args:
#         prefix: キャッシュキーのプレフィックス
#         **kwargs: キーに含めるパラメータ

#     Returns:
#         str: 生成されたキャッシュキー
#     """
#     # パラメータを安定したJSONに変換
#     params_str = json.dumps(kwargs, sort_keys=True)
#     # キーハッシュを生成（短くするため）
#     key_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]  # 衝突確率を下げるため12文字に拡張
#     return f"{prefix}:{key_hash}"


# def get_trending_keywords(
#     db: Session, limit: int = 20, year_month: str = None, months: int = None
# ) -> List[Dict]:
#     """
#     指定期間の投稿から、トレンドキーワードを抽出
#     結果をキャッシュして高速化（1時間有効）

#     Args:
#         db: データベースセッション
#         limit: 返すキーワードの最大数
#         year_month: 分析開始年月（YYYY-MM形式）
#         months: 分析期間（月数）

#     Returns:
#         List[Dict]: キーワードと出現回数のリスト
#     """
#     # キャッシュキーを作成
#     cache_key = get_cache_key(
#         "trending_keywords", limit=limit, year_month=year_month, months=months
#     )

#     # キャッシュをチェック
#     cached_result = cache.get(cache_key)
#     if cached_result:
#         return cached_result

#     # クエリビルダー
#     query = db.query(InfluencerPost)

#     # フィルター条件適用
#     if year_month is not None and months is not None:
#         # 年月指定の場合（YYYY-MM形式を解析）
#         try:
#             start_year, start_month = map(int, year_month.split("-"))
#             start_date = datetime(start_year, start_month, 1)
#             # 月数を加算して終了日を計算
#             if start_month + months <= 12:
#                 end_date = datetime(start_year, start_month + months, 1)
#             else:
#                 years_to_add = (start_month + months - 1) // 12
#                 end_month = (start_month + months - 1) % 12 + 1
#                 end_date = datetime(start_year + years_to_add, end_month, 1)

#             query = query.filter(
#                 InfluencerPost.post_date >= start_date,
#                 InfluencerPost.post_date < end_date,
#             )
#         except (ValueError, TypeError) as e:
#             raise HTTPException(
#                 status_code=400, detail=f"無効な年月形式です。YYYY-MM形式で指定してください: {str(e)}"
#             )

#     # 期間内の投稿を取得
#     posts = query.all()

#     if not posts:
#         return []

#     # キャッシュ制御用の最終更新日時チェック
#     _ = db.query(func.max(InfluencerPost.updated_at)).scalar()

#     # 投稿から名詞を抽出（並行処理で高速化）
#     all_nouns = []

#     def process_text(text):
#         try:
#             if text:
#                 return extract_nouns(text)
#             return []
#         except Exception:
#             return []

#     # パフォーマンス最適化: チャンクサイズを調整して大量データでの効率を向上
#     import os

#     # CPU数に基づいてワーカー数を調整 (ただし最大値を設定)
#     max_workers = min(os.cpu_count() or 4, 16)

#     # 投稿をバッチ処理するためにリスト分割
#     def chunks(lst, n):
#         for i in range(0, len(lst), n):
#             yield lst[i : i + n]

#     # 大規模データセット用の最適化: 投稿を小さなバッチに分割して処理
#     valid_posts = [post for post in posts if post.text]
#     total_posts = len(valid_posts)

#     if total_posts == 0:
#         return []

#     # データ量に応じて処理方法を選択
#     if total_posts < 100:
#         # 少量データの場合は直接処理
#         with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#             future_to_text = {
#                 executor.submit(process_text, post.text): post for post in valid_posts
#             }

#             for future in concurrent.futures.as_completed(future_to_text):
#                 try:
#                     result = future.result()
#                     all_nouns.extend(result)
#                 except Exception:
#                     pass
#     else:
#         # 大量データの場合はバッチ処理
#         # 適切なバッチサイズを計算 (ワーカー数の倍数)
#         batch_size = 50
#         batches = list(chunks(valid_posts, batch_size))

#         for batch in batches:
#             with concurrent.futures.ThreadPoolExecutor(
#                 max_workers=max_workers
#             ) as executor:
#                 futures = [executor.submit(process_text, post.text) for post in batch]
#                 for future in concurrent.futures.as_completed(futures):
#                     try:
#                         result = future.result()
#                         all_nouns.extend(result)
#                     except Exception:
#                         pass

#     # カウント、ソート、整形
#     counter = Counter(all_nouns)
#     top_keywords = counter.most_common(limit)
#     result = [{"word": word, "count": count} for word, count in top_keywords]

#     # キャッシュ保存（1時間）
#     cache.set(cache_key, result, ttl_seconds=3600)

#     return result


# def analyze_keywords_by_engagement(
#     db: Session, engagement_type: str = "likes", limit: int = 20
# ) -> List[Dict]:
#     """
#     エンゲージメント（いいね数またはコメント数）が高い投稿から特徴的なキーワードを抽出
#     結果をキャッシュして高速化（1時間有効）

#     Args:
#         db: データベースセッション
#         engagement_type: 分析対象のエンゲージメント種別 ("likes" または "comments")
#         limit: 返すキーワードの最大数

#     Returns:
#         List[Dict]: キーワードと出現回数のリスト

#     Raises:
#         ValueError: engagement_typeが不正な場合
#     """
#     if engagement_type not in ["likes", "comments"]:
#         raise ValueError("engagement_type must be 'likes' or 'comments'")

#     # キャッシュキーを作成
#     cache_key = get_cache_key(
#         "engagement_keywords", engagement_type=engagement_type, limit=limit
#     )

#     # キャッシュをチェック
#     cached_result = cache.get(cache_key)
#     if cached_result:
#         return cached_result

#     # エンゲージメントが高い順に投稿を取得（上位100件程度）
#     if engagement_type == "likes":
#         posts = (
#             db.query(InfluencerPost)
#             .order_by(InfluencerPost.likes.desc())
#             .limit(100)
#             .all()
#         )
#     else:  # comments
#         posts = (
#             db.query(InfluencerPost)
#             .order_by(InfluencerPost.comments.desc())
#             .limit(100)
#             .all()
#         )

#     if not posts:
#         return []

#     # 名詞を抽出（並行処理）
#     all_nouns = []

#     def process_text(text):
#         if text:
#             return extract_nouns(text)
#         return []

#     # パフォーマンス最適化: CPU数に基づいてワーカー数を調整
#     import os

#     max_workers = min(os.cpu_count() or 4, 12)

#     valid_posts = [post for post in posts if post.text]
#     if not valid_posts:
#         return []

#     with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#         future_to_text = {
#             executor.submit(process_text, post.text): post for post in valid_posts
#         }

#         for future in concurrent.futures.as_completed(future_to_text):
#             try:
#                 result = future.result()
#                 all_nouns.extend(result)
#             except Exception as e:
#                 import logging

#                 logging.getLogger("app").warning(f"Error processing text: {str(e)}")

#     # カウント、ソート、整形
#     counter = Counter(all_nouns)
#     top_keywords = counter.most_common(limit)
#     result = [{"word": word, "count": count} for word, count in top_keywords]

#     # キャッシュ保存（1時間）
#     cache.set(cache_key, result, ttl_seconds=3600)

#     return result
