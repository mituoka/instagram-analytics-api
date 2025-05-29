from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# インフルエンサー投稿のスキーマ
class InfluencerPostBase(BaseModel):
    influencer_id: int
    post_id: int
    shortcode: str
    likes: int
    comments: int
    thumbnail: Optional[str] = None
    text: Optional[str] = None
    post_date: datetime


# データベースから取得した投稿のスキーマ
class InfluencerPost(InfluencerPostBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# 統計情報のスキーマ
class InfluencerStats(BaseModel):
    influencer_id: int
    avg_likes: float = Field(..., description="平均いいね数")
    avg_comments: float = Field(..., description="平均コメント数")
    total_posts: int = Field(..., description="投稿数")


# ランキング用のスキーマ
class InfluencerRanking(BaseModel):
    influencer_id: int
    avg_value: float = Field(..., description="平均値（いいね数またはコメント数）")
    total_posts: int = Field(..., description="投稿数")


# キーワード出現回数のスキーマ
class KeywordCount(BaseModel):
    word: str = Field(..., description="抽出された名詞")
    count: int = Field(..., description="出現回数")


# キーワード分析レスポンスのスキーマ
class KeywordAnalysisResponse(BaseModel):
    keywords: list[KeywordCount] = Field(..., description="キーワード一覧と出現回数")
    total_analyzed_posts: int = Field(..., description="分析対象となった投稿の総数")
    time_period_days: Optional[int] = Field(None, description="分析対象期間（日数）")


# 高エンゲージメントキーワード分析のスキーマ
class EngagementKeywordsResponse(BaseModel):
    keywords: list[KeywordCount] = Field(..., description="キーワード一覧と出現回数")
    engagement_type: str = Field(..., description="エンゲージメント種別（likes または comments）")
    total_analyzed_posts: int = Field(..., description="分析対象となった投稿の総数")
