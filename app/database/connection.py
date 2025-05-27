import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DB接続設定: 環境変数 or デフォルト値
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/instagram_analytics")

# SQLAlchemyエンジン設定
engine = create_engine(
    DATABASE_URL,
    echo=bool(os.getenv("SQL_ECHO", "False").lower() == "true"),  # SQLログ出力
    pool_pre_ping=True,  # 接続確認
    pool_recycle=3600    # 1時間ごとに接続リサイクル
)

# DBセッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデル定義の基底クラス
Base = declarative_base()

# FastAPI依存性注入用DBセッション
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()