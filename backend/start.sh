#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Bootstrapping database..."
python -m app.database.bootstrap

echo "Starting Celery worker in the background..."
celery -A app.workers.celery_app worker --loglevel=info &

echo "Starting Uvicorn web server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
