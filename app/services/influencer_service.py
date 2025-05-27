"""
インフルエンサーデータの取得と分析を行うサービスレイヤー
"""
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.database_models import InfluencerPost


def get_influencer_stats(db: Session, influencer_id: int):
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
    # インフルエンサーの統計情報を取得するクエリ
    result = db.query(
        func.avg(InfluencerPost.likes).label("avg_likes"),
        func.avg(InfluencerPost.comments).label("avg_comments"),
        func.count(InfluencerPost.id).label("total_posts")
    ).filter(
        InfluencerPost.influencer_id == influencer_id
    ).first()
    
    # 該当するインフルエンサーの投稿が見つからない場合
    if not result or result.total_posts == 0:
        raise HTTPException(
            status_code=404, 
            detail=f"Influencer with ID {influencer_id} not found"
        )
    
    # 結果を辞書で返す
    return {
        "influencer_id": influencer_id,
        "avg_likes": float(result.avg_likes),
        "avg_comments": float(result.avg_comments),
        "total_posts": result.total_posts
    }


def get_top_influencers_by_likes(db: Session, limit: int = 10):
    """
    平均いいね数の多い順にインフルエンサーをランキング
    
    Args:
        db: データベースセッション
        limit: 取得する上位件数（デフォルト: 10）
        
    Returns:
        list: インフルエンサーのランキングリスト
    """
    results = db.query(
        InfluencerPost.influencer_id,
        func.avg(InfluencerPost.likes).label("avg_likes"),
        func.count(InfluencerPost.id).label("total_posts")
    ).group_by(
        InfluencerPost.influencer_id
    ).order_by(
        func.avg(InfluencerPost.likes).desc()
    ).limit(limit).all()
    
    return [
        {
            "influencer_id": result.influencer_id,
            "avg_value": float(result.avg_likes),
            "total_posts": result.total_posts
        }
        for result in results
    ]


def get_top_influencers_by_comments(db: Session, limit: int = 10):
    """
    平均コメント数の多い順にインフルエンサーをランキング
    
    Args:
        db: データベースセッション
        limit: 取得する上位件数（デフォルト: 10）
        
    Returns:
        list: インフルエンサーのランキングリスト
    """
    results = db.query(
        InfluencerPost.influencer_id,
        func.avg(InfluencerPost.comments).label("avg_comments"),
        func.count(InfluencerPost.id).label("total_posts")
    ).group_by(
        InfluencerPost.influencer_id
    ).order_by(
        func.avg(InfluencerPost.comments).desc()
    ).limit(limit).all()
    
    return [
        {
            "influencer_id": result.influencer_id,
            "avg_value": float(result.avg_comments),
            "total_posts": result.total_posts
        }
        for result in results
    ]
    
    return [
        {
            "influencer_id": result.influencer_id,
            "avg_value": float(result.avg_comments),
            "total_posts": result.total_posts
        }
        for result in results
    ]