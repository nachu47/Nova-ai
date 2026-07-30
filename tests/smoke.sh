#!/usr/bin/env sh
set -eu
BASE_URL="${BASE_URL:-http://localhost}"
curl -fsS "$BASE_URL/api/v1/health/ready" | grep -q 'ready'
curl -fsS "$BASE_URL/" >/dev/null
printf 'Nova smoke test passed.\n'
