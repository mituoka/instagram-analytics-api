#!/bin/bash
# Instagram Analytics API 起動スクリプト
set -e

# Pythonパスを設定
export PYTHONPATH=/app:$PYTHONPATH

# データベース接続を待機
echo "Waiting for database connection..."
sleep 5

# マイグレーションの実行（開発環境ではスキップ）
if [ "$DEBUG" != "true" ]; then
  echo "Running database migrations..."
  cd /app && python -m alembic upgrade head || echo "Migration failed, but continuing..."
fi

# サーバーの起動
echo "Starting API server..."
WORKERS=${MAX_WORKERS:-1}
echo "Using $WORKERS worker(s)"

# uvicorn サーバーの起動
# デバッグモード確認
if [ "$DEBUG" = "true" ]; then
  echo "Starting in DEBUG mode"
  exec uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000} --reload
else
  echo "Starting in PRODUCTION mode"
  exec uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000} --workers $WORKERS
fi
