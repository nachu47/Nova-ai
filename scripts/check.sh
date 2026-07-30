#!/usr/bin/env sh
set -eu
python -m compileall -q backend/app backend/tests
python -m json.tool docker/grafana/dashboards/nova-overview.json >/dev/null
if command -v docker >/dev/null 2>&1; then docker compose config >/dev/null; fi
printf 'Static checks passed.\n'
