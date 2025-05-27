from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Alembicの設定オブジェクト
config = context.config

# 環境変数からDB接続情報を取得（存在する場合）
db_url = os.getenv("DATABASE_URL")
if db_url:
    # 環境変数の値で設定を上書き
    config.set_main_option("sqlalchemy.url", db_url)

# ログ設定
fileConfig(config.config_file_name)

# モデル定義をインポートするためにプロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.base import Base

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """オフラインモードでマイグレーションを実行

    データベースへの実際の接続なしでマイグレーションスクリプトを生成します。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """オンラインモードでマイグレーションを実行

    実際のデータベース接続を使用してマイグレーションを実行します。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
