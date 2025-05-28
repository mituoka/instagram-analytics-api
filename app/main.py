from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import influencer, analytics
from app.models import base
from app.database.connection import engine

# 開発環境ではテーブル自動作成（本番環境ではAlembicでマイグレーション管理を推奨）
base.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Instagram Analytics API",
    description="Instagram influencer data analysis API",
    version="0.1.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(
    influencer.router, prefix="/api/v1/influencers", tags=["influencers"]
)
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Instagram Analytics API!"}
