"""
インフルエンサー投稿データへのアクセスを担当するリポジトリクラス
データアクセス層のカプセル化を提供します
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.database_models import InfluencerPost


class InfluencerPostRepository:
    """
    インフルエンサー投稿データへのアクセスを提供するリポジトリクラス
    データベース操作をカプセル化し、サービスレイヤーに簡潔なインターフェースを提供
    """

    def __init__(self, db: Session):
        """
        コンストラクタ

        Args:
            db: SQLAlchemy データベースセッション
        """
        self.db = db

    def get_by_influencer_id(self, influencer_id: int) -> List[InfluencerPost]:
        """
        指定されたインフルエンサーIDの全投稿を取得

        Args:
            influencer_id: インフルエンサーID

        Returns:
            List[InfluencerPost]: 投稿のリスト
        """
        return (
            self.db.query(InfluencerPost)
            .filter(InfluencerPost.influencer_id == influencer_id)
            .all()
        )

    def get_influencer_stats(self, influencer_id: int):
        """
        インフルエンサーの統計情報を取得

        Args:
            influencer_id: インフルエンサーID

        Returns:
            タプル: (平均いいね数, 平均コメント数, 投稿数)
            存在しない場合はNone
        """
        result = (
            self.db.query(
                func.avg(InfluencerPost.likes).label("avg_likes"),
                func.avg(InfluencerPost.comments).label("avg_comments"),
                func.count(InfluencerPost.id).label("total_posts"),
            )
            .filter(InfluencerPost.influencer_id == influencer_id)
            .first()
        )

        if not result or result.total_posts == 0:
            return None

        return result

    def get_top_by_likes(self, limit: int = 10):
        """
        平均いいね数の多い順にインフルエンサーをランキング

        Args:
            limit: 取得する上位件数

        Returns:
            list: インフルエンサーのランキングデータ
        """
        return (
            self.db.query(
                InfluencerPost.influencer_id,
                func.avg(InfluencerPost.likes).label("avg_likes"),
                func.count(InfluencerPost.id).label("total_posts"),
            )
            .group_by(InfluencerPost.influencer_id)
            .order_by(func.avg(InfluencerPost.likes).desc())
            .limit(limit)
            .all()
        )

    def get_top_by_comments(self, limit: int = 10):
        """
        平均コメント数の多い順にインフルエンサーをランキング

        Args:
            limit: 取得する上位件数

        Returns:
            list: インフルエンサーのランキングデータ
        """
        return (
            self.db.query(
                InfluencerPost.influencer_id,
                func.avg(InfluencerPost.comments).label("avg_comments"),
                func.count(InfluencerPost.id).label("total_posts"),
            )
            .group_by(InfluencerPost.influencer_id)
            .order_by(func.avg(InfluencerPost.comments).desc())
            .limit(limit)
            .all()
        )

    def get_recent_posts_by_date(self, days: int = 30):
        """
        指定された日数以内の投稿を取得

        Args:
            days: さかのぼる日数

        Returns:
            List[InfluencerPost]: 投稿のリスト
        """
        cut_off_date = datetime.now() - timedelta(days=days)

        return (
            self.db.query(InfluencerPost)
            .filter(InfluencerPost.post_date >= cut_off_date)
            .all()
        )

    def get_posts_by_engagement(self, engagement_type: str = "likes", limit: int = 100):
        """
        エンゲージメント（いいね数またはコメント数）が高い順に投稿を取得

        Args:
            engagement_type: 'likes'または'comments'
            limit: 取得する上位件数

        Returns:
            List[InfluencerPost]: 投稿のリスト

        Raises:
            ValueError: engagement_typeが不正な場合
        """
        if engagement_type not in ["likes", "comments"]:
            raise ValueError("engagement_type must be 'likes' or 'comments'")

        if engagement_type == "likes":
            return (
                self.db.query(InfluencerPost)
                .order_by(InfluencerPost.likes.desc())
                .limit(limit)
                .all()
            )
        else:  # "comments"
            return (
                self.db.query(InfluencerPost)
                .order_by(InfluencerPost.comments.desc())
                .limit(limit)
                .all()
            )

    def get_latest_update_time(self, influencer_id: Optional[int] = None):
        """
        最新の更新日時を取得（キャッシュ制御用）

        Args:
            influencer_id: 特定のインフルエンサーIDに限定する場合

        Returns:
            datetime: 最新の更新日時、または投稿がない場合はNone
        """
        query = self.db.query(func.max(InfluencerPost.updated_at))

        if influencer_id:
            query = query.filter(InfluencerPost.influencer_id == influencer_id)

        return query.scalar()
