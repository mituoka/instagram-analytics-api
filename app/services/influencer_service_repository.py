"""
サービスレイヤーからリポジトリを使用するように拡張したインフルエンサーサービス
リポジトリパターンを採用することでデータアクセスレイヤーとビジネスロジックを分離
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict, Any

from app.database.repositories import InfluencerPostRepository


def get_influencer_stats(db: Session, influencer_id: int) -> Dict[str, Any]:
    """
    指定されたインフルエンサーIDの統計情報を取得する

    Args:
        db: データベースセッション
        influencer_id: インフルエンサーID

    Returns:
        dict: 統計情報（平均いいね数、平均コメント数、投稿数）

    Raises:
        HTTPException: インフルエンサーIDに該当する投稿が見つからない場合
    """
    # リポジトリをインスタンス化
    repository = InfluencerPostRepository(db)

    # インフルエンサーの統計情報を取得
    stats = repository.get_influencer_stats(influencer_id)

    # 該当するインフルエンサーの投稿が見つからない場合
    if not stats:
        raise HTTPException(
            status_code=404, detail=f"Influencer with ID {influencer_id} not found"
        )

    # 結果を辞書で返す
    return {
        "influencer_id": influencer_id,
        "avg_likes": float(stats.avg_likes),
        "avg_comments": float(stats.avg_comments),
        "total_posts": stats.total_posts,
    }


def get_top_influencers_by_likes(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """
    平均いいね数の多い順にインフルエンサーをランキング

    Args:
        db: データベースセッション
        limit: 取得する上位件数（デフォルト: 10）

    Returns:
        list: インフルエンサーのランキングリスト
    """
    # リポジトリをインスタンス化
    repository = InfluencerPostRepository(db)

    # いいね数の多い順にランキング取得
    results = repository.get_top_by_likes(limit)

    return [
        {
            "influencer_id": result.influencer_id,
            "avg_value": float(result.avg_likes),
            "total_posts": result.total_posts,
        }
        for result in results
    ]


def get_top_influencers_by_comments(
    db: Session, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    平均コメント数の多い順にインフルエンサーをランキング

    Args:
        db: データベースセッション
        limit: 取得する上位件数（デフォルト: 10）

    Returns:
        list: インフルエンサーのランキングリスト
    """
    # リポジトリをインスタンス化
    repository = InfluencerPostRepository(db)

    # コメント数の多い順にランキング取得
    results = repository.get_top_by_comments(limit)

    return [
        {
            "influencer_id": result.influencer_id,
            "avg_value": float(result.avg_comments),
            "total_posts": result.total_posts,
        }
        for result in results
    ]
