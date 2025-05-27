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

    class Config:
        from_attributes = True  # pydantic v2では orm_mode の代わりに from_attributes を使用


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
