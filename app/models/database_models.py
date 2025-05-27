from sqlalchemy import Column, Integer, String, BigInteger, Text, DateTime, func
from app.models.base import Base


class InfluencerPost(Base):
    """インフルエンサー投稿を表すSQLAlchemyモデル"""

    __tablename__ = "influencer_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    influencer_id = Column(Integer, nullable=False, index=True)
    post_id = Column(BigInteger, nullable=False, unique=True)
    shortcode = Column(String(50), nullable=False)
    likes = Column(Integer, nullable=False, default=0)
    comments = Column(Integer, nullable=False, default=0)
    thumbnail = Column(Text)
    text = Column(Text)
    post_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<InfluencerPost(id={self.id}, influencer_id={self.influencer_id}, post_id={self.post_id})>"
