"""
テキスト分析機能を提供するサービスレイヤー
日本語の形態素解析、名詞抽出、キーワードカウントなどの機能を提供します
パフォーマンス最適化（キャッシュ、並行処理）を実装
"""

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
from datetime import datetime, timedelta

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

    # テキストをトークン化し、名詞のみを取得
    tokens = tokenizer.tokenize(content)
    nouns = []

    for token in tokens:
        # 形態素解析結果から品詞情報を取得
        pos = token.part_of_speech.split(",")[0]

        # 名詞であるか確認（一般名詞、固有名詞、複合名詞など）
        if pos == "名詞":
            # 1文字の名詞は除外（ノイズになることが多いため）
            # ただし、記号や数字のみの場合も除外
            surface = token.surface
            if len(surface) > 1 and not re.match(r"^[0-9０-９]+$", surface):
                nouns.append(surface)

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

    # すべての投稿から名詞を抽出して出現頻度をカウント（並行処理で高速化）
    all_nouns = []

    # テキスト分析を並行処理する関数
    def process_text(text):
        if text:
            return extract_nouns(text)
        return []

    # 並行処理でテキスト分析を実行
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # 投稿テキストを並行して処理
        future_to_text = {
            executor.submit(process_text, post.text): post
            for post in posts
            if post.text
        }

        # 結果を収集
        for future in concurrent.futures.as_completed(future_to_text):
            all_nouns.extend(future.result())

    # 名詞の出現頻度をカウント
    counter = Counter(all_nouns)

    # 出現頻度の多い順にlimit個取得
    top_keywords = counter.most_common(limit)

    # 結果を整形
    result = [{"word": word, "count": count} for word, count in top_keywords]

    # 結果をキャッシュ（30分 = 1800秒）
    cache.set(cache_key, result, ttl_seconds=1800)

    return result


def get_cache_key(prefix: str, **kwargs) -> str:
    """
    キャッシュキーを生成する関数

    Args:
        prefix: キャッシュキーのプレフィックス
        **kwargs: キーに含めるパラメータ

    Returns:
        str: 生成されたキャッシュキー
    """
    # パラメータを安定したJSONに変換
    params_str = json.dumps(kwargs, sort_keys=True)
    # キーハッシュを生成（短くするため）
    key_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    return f"{prefix}:{key_hash}"


def get_trending_keywords(db: Session, days: int = 30, limit: int = 20) -> List[Dict]:
    """
    過去N日間の投稿から、トレンドキーワードを抽出
    結果をキャッシュして高速化（1時間有効）

    Args:
        db: データベースセッション
        days: 過去何日分のデータを分析するか
        limit: 返すキーワードの最大数

    Returns:
        List[Dict]: キーワードと出現回数のリスト
    """
    # キャッシュキーを作成
    cache_key = get_cache_key("trending_keywords", days=days, limit=limit)

    # キャッシュをチェック
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    # 過去N日間の投稿を取得（日時フィルタリングを追加）
    # Pythonで日付計算を行い、SQLに渡す
    cut_off_date = datetime.now() - timedelta(days=days)
    posts = (
        db.query(InfluencerPost).filter(InfluencerPost.post_date >= cut_off_date).all()
    )

    if not posts:
        return []

    # 最終更新日時をチェック（将来的にキャッシュ無効化に使用）
    # Pythonで日付計算を行い、SQLに渡す
    cut_off_date = datetime.now() - timedelta(days=days)
    _ = (
        db.query(func.max(InfluencerPost.updated_at))
        .filter(InfluencerPost.post_date >= cut_off_date)
        .scalar()
    )

    # すべての投稿から名詞を抽出して出現頻度をカウント（並行処理で高速化）
    all_nouns = []

    # テキスト分析を並行処理する関数
    def process_text(text):
        if text:
            return extract_nouns(text)
        return []

    # 並行処理でテキスト分析を実行（最大10ワーカー）
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # 投稿テキストを並行して処理
        future_to_text = {
            executor.submit(process_text, post.text): post
            for post in posts
            if post.text
        }

        # 結果を収集
        for future in concurrent.futures.as_completed(future_to_text):
            all_nouns.extend(future.result())

    # 名詞の出現頻度をカウント
    counter = Counter(all_nouns)

    # 出現頻度の多い順にlimit個取得
    top_keywords = counter.most_common(limit)

    # 結果を整形
    result = [{"word": word, "count": count} for word, count in top_keywords]

    # 結果をキャッシュ（1時間 = 3600秒）
    cache.set(cache_key, result, ttl_seconds=3600)

    return result


def analyze_keywords_by_engagement(
    db: Session, engagement_type: str = "likes", limit: int = 20
) -> List[Dict]:
    """
    エンゲージメント（いいね数またはコメント数）が高い投稿から特徴的なキーワードを抽出
    結果をキャッシュして高速化（1時間有効）

    Args:
        db: データベースセッション
        engagement_type: 分析対象のエンゲージメント種別 ("likes" または "comments")
        limit: 返すキーワードの最大数

    Returns:
        List[Dict]: キーワードと出現回数のリスト

    Raises:
        ValueError: engagement_typeが不正な場合
    """
    if engagement_type not in ["likes", "comments"]:
        raise ValueError("engagement_type must be 'likes' or 'comments'")

    # キャッシュキーを作成
    cache_key = get_cache_key(
        "engagement_keywords", engagement_type=engagement_type, limit=limit
    )

    # キャッシュをチェック
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    # エンゲージメントが高い順に投稿を取得（上位100件程度）
    if engagement_type == "likes":
        posts = (
            db.query(InfluencerPost)
            .order_by(InfluencerPost.likes.desc())
            .limit(100)
            .all()
        )
    else:  # comments
        posts = (
            db.query(InfluencerPost)
            .order_by(InfluencerPost.comments.desc())
            .limit(100)
            .all()
        )

    if not posts:
        return []

    # すべての投稿から名詞を抽出して出現頻度をカウント（並行処理で高速化）
    all_nouns = []

    # テキスト分析を並行処理する関数
    def process_text(text):
        if text:
            return extract_nouns(text)
        return []

    # 並行処理でテキスト分析を実行（最大8ワーカー）
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # 投稿テキストを並行して処理
        future_to_text = {
            executor.submit(process_text, post.text): post
            for post in posts
            if post.text
        }

        # 結果を収集
        for future in concurrent.futures.as_completed(future_to_text):
            all_nouns.extend(future.result())

    # 名詞の出現頻度をカウント
    counter = Counter(all_nouns)

    # 出現頻度の多い順にlimit個取得
    top_keywords = counter.most_common(limit)

    # 結果を整形
    result = [{"word": word, "count": count} for word, count in top_keywords]

    # 結果をキャッシュ（1時間 = 3600秒）
    cache.set(cache_key, result, ttl_seconds=3600)

    return result
