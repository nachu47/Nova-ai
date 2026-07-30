#!/usr/bin/env sh
set -eu

if [ "${1:-}" = "uvicorn" ]; then
  alembic upgrade head
  python -m app.database.bootstrap
fi
exec "$@"
