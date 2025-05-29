"""
インフルエンサーデータのAPIエンドポイント
"""

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.schemas import InfluencerStats, InfluencerRanking
from app.services import influencer_service

# ルーター定義
router = APIRouter()


@router.get(
    "/{influencer_id}/stats",
    response_model=InfluencerStats,
    summary="インフルエンサーの統計情報取得",
)
def get_influencer_stats(
    influencer_id: int = Path(..., description="インフルエンサーID", ge=1),
    db: Session = Depends(get_db),
):
    """
    指定されたインフルエンサーIDの統計情報を取得します。

    - **influencer_id**: 統計情報を取得したいインフルエンサーのID

    戻り値:
    - **平均いいね数**: インフルエンサーの投稿平均いいね数
    - **平均コメント数**: インフルエンサーの投稿平均コメント数
    - **投稿数**: 分析対象の投稿数
    """
    return influencer_service.get_influencer_stats(db, influencer_id)


@router.get(
    "/ranking/likes",
    response_model=List[InfluencerRanking],
    summary="いいね数ランキング取得",
)
def get_likes_ranking(
    limit: int = Query(10, description="取得するランキング数", ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    平均いいね数の多い順にインフルエンサーをランキングします。

    - **limit**: 取得するランキング数（最大100）

    戻り値:
    - **インフルエンサーID**: ランキング対象のインフルエンサーID
    - **平均値**: 平均いいね数
    - **投稿数**: 分析対象の投稿数
    """
    return influencer_service.get_top_influencers_by_likes(db, limit)


@router.get(
    "/ranking/comments",
    response_model=List[InfluencerRanking],
    summary="コメント数ランキング取得",
)
def get_comments_ranking(
    limit: int = Query(10, description="取得するランキング数", ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    平均コメント数の多い順にインフルエンサーをランキングします。

    - **limit**: 取得するランキング数（最大100）

    戻り値:
    - **インフルエンサーID**: ランキング対象のインフルエンサーID
    - **平均値**: 平均コメント数
    - **投稿数**: 分析対象の投稿数
    """
    return influencer_service.get_top_influencers_by_comments(db, limit)
