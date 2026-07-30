# Installation

## Requirements

- Docker Engine with the Compose v2 plugin
- 4 GB RAM minimum; 8 GB recommended when Grafana is enabled
- Ports 80, 3001 and 9090 available for local mode; port 443 for the TLS override

## Local installation

```bash
cp .env.example .env
docker compose up --build
```

The backend entrypoint applies Alembic migrations and creates the idempotent demo administrator and receptionist agent. PostgreSQL, Redis, recordings, Prometheus, and Grafana use named volumes.

## Verify

```bash
curl -fsS http://localhost/api/v1/health/live
curl -fsS http://localhost/api/v1/health/ready
./tests/smoke.sh
```

## Development without the edge NGINX container

```bash
# backend
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

Set `DATABASE_URL` and `REDIS_URL` to reachable local services when running outside Compose.
