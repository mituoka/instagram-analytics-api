"""
インフルエンサーデータの分析APIエンドポイント
テキスト分析機能を提供します
"""

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database.connection import get_db
from app.services import text_analysis_service
from app.models.schemas import (
    KeywordAnalysisResponse,
    EngagementKeywordsResponse,
)
from app.models.database_models import InfluencerPost

# ルーター定義
router = APIRouter()


@router.get(
    "/{influencer_id}/keywords",
    response_model=KeywordAnalysisResponse,
    summary="インフルエンサーの投稿で頻出する名詞を抽出",
)
def get_influencer_keywords(
    influencer_id: int = Path(..., description="インフルエンサーID", ge=1),
    limit: int = Query(20, description="取得するキーワード数", ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    指定されたインフルエンサーの投稿テキストから頻出する名詞を抽出します。

    - **influencer_id**: 分析対象のインフルエンサーID
    - **limit**: 返すキーワードの最大数（1〜100の範囲、デフォルト20）

    形態素解析を使用して日本語テキストを適切に分析し、名詞のみを抽出して頻度をカウントします。
    """
    try:
        # インフルエンサーのキーワード頻度を取得
        keywords = text_analysis_service.get_influencer_keywords(
            db, influencer_id, limit
        )

        # 投稿数を取得
        posts_count = (
            db.query(func.count(InfluencerPost.id))
            .filter(InfluencerPost.influencer_id == influencer_id)
            .scalar()
            or 0
        )

        return KeywordAnalysisResponse(
            keywords=keywords, total_analyzed_posts=posts_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing keywords: {str(e)}"
        )


# @router.get(
#     "/trending-keywords",
#     response_model=KeywordAnalysisResponse,
#     summary="トレンドキーワードの抽出",
# )
# def get_trending_keywords(
#     limit: int = Query(20, description="取得するキーワード数", ge=1, le=100),
#     year_month: Optional[str] = Query(
#         None, description="分析開始年月（YYYY-MM形式）", pattern=r"^\d{4}-\d{2}$"
#     ),
#     months: Optional[int] = Query(None, description="分析期間（月数）", ge=1, le=36),
#     db: Session = Depends(get_db),
# ):
#     """
#     指定期間の投稿から、トレンドキーワード（頻出名詞）を抽出します。
#
#     指定方法:
#     - **year_month**: 分析開始年月（YYYY-MM形式）
#     - **months**: 分析期間（月数、1〜36ヶ月）
#
#     パラメータ未指定時は過去全ての投稿データを分析します。
#
#     - **limit**: 返すキーワードの最大数（1〜100の範囲、デフォルト20）
#
#     形態素解析を使用して日本語テキストを適切に分析し、名詞のみを抽出して頻度をカウントします。
#     """
#     try:
#         # パラメータの組み合わせチェック
#         if (year_month is not None and months is None) or (
#             year_month is None and months is not None
#         ):
#             raise HTTPException(
#                 status_code=400, detail="year_monthとmonthsは一緒に指定する必要があります"
#             )
#
#         # トレンドキーワードを取得
#         try:
#             keywords = text_analysis_service.get_trending_keywords(
#                 db, limit=limit, year_month=year_month, months=months
#             )
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500, detail=f"Error analyzing trending keywords: {str(e)}"
#             )
#
#         # 投稿数を取得
#         from sqlalchemy import func
#         from app.models.database_models import InfluencerPost
#         from datetime import datetime
#
#         query = db.query(func.count(InfluencerPost.id))
#
#         if year_month is not None and months is not None:
#             start_year, start_month = map(int, year_month.split("-"))
#             start_date = datetime(start_year, start_month, 1)
#
#             # 月数を加算して終了日を計算
#             if start_month + months <= 12:
#                 end_date = datetime(start_year, start_month + months, 1)
#             else:
#                 years_to_add = (start_month + months - 1) // 12
#                 end_month = (start_month + months - 1) % 12 + 1
#                 end_date = datetime(start_year + years_to_add, end_month, 1)
#
#             query = query.filter(
#                 InfluencerPost.post_date >= start_date,
#                 InfluencerPost.post_date < end_date,
#             )
#             # 概算の日数
#             time_period_days = (end_date - start_date).days
#         else:
#             # 全期間の場合
#             time_period_days = None
#
#         posts_count = query.scalar() or 0
#
#         return KeywordAnalysisResponse(
#             keywords=keywords,
#             total_analyzed_posts=posts_count,
#             time_period_days=time_period_days,
#             start_year_month=year_month,
#             months=months,
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Error analyzing trending keywords: {str(e)}"
#         )


# @router.get(
#     "/keywords/engagement",
#     response_model=EngagementKeywordsResponse,
#     summary="高エンゲージメント投稿のキーワード分析",
# )
# def get_engagement_keywords(
#     engagement_type: str = Query(
#         "likes",
#         description="分析対象のエンゲージメント種別",
#         pattern="^(likes|comments)$",
#     ),
#     limit: int = Query(20, description="取得するキーワード数", ge=1, le=100),
#     db: Session = Depends(get_db),
# ):
#     """
#     エンゲージメント（いいね数またはコメント数）が高い投稿から特徴的なキーワードを抽出します。
#
#     - **engagement_type**: 分析対象のエンゲージメント種別 ("likes"または"comments")
#     - **limit**: 返すキーワードの最大数（1〜100の範囲、デフォルト20）
#
#     高いエンゲージメントを獲得している投稿に共通するキーワードを分析することで、
#     効果的な投稿内容の傾向を把握できます。
#     """
#     try:
#         # エンゲージメントが高い投稿のキーワードを分析
#         keywords = text_analysis_service.analyze_keywords_by_engagement(
#             db, engagement_type, limit
#         )
#
#         # 分析対象の投稿数（上位100件）
#         count_value = db.query(func.count()).select_from(InfluencerPost).scalar()
#         if isinstance(count_value, int):
#             total_posts = min(count_value or 0, 100)
#         else:
#             total_posts = 100
#
#         return EngagementKeywordsResponse(
#             keywords=keywords,
#             engagement_type=engagement_type,
#             total_analyzed_posts=total_posts,
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Error analyzing engagement keywords: {str(e)}"
#         )
