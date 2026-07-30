# Validation report

Generated and audited on 26 July 2026.

## Passed checks

- Python source and test compilation completed without syntax errors.
- Backend API suite: **7 tests passed**, including authentication, refresh-token rotation/reuse containment, API-key scopes, agents, CRM, mock calls, health checks, and outbound URL policy.
- SQLAlchemy metadata created successfully on a clean validation database: **27 relational tables**.
- FastAPI OpenAPI generation completed: **91 application routes** and **67 documented HTTP paths**.
- TypeScript/TSX syntax transpilation completed for **34 source and test files**.
- Docker Compose, CI, Prometheus, Grafana provisioning, and dashboard JSON parsed successfully.
- HTTP edge NGINX, TLS edge NGINX, and frontend NGINX configurations passed syntax validation.
- Shell entrypoint/check/smoke scripts passed shell syntax validation.
- No `TODO`, `FIXME`, `Implement later`, or `Your code here` markers remain.

## Environment limitations

- The generation environment does not provide the Docker CLI, so `docker compose build` and a live multi-container startup could not be executed here.
- Access to the npm registry timed out, so dependency-resolved frontend lint, Vitest, and Vite production build could not be executed here. The repository CI and Docker build run those commands in a normal networked environment.
- Several external Python integration packages were unavailable from the generation environment's package index. Backend tests therefore used temporary import stand-ins for those unavailable provider packages; those stand-ins are not included in this repository. The backend Dockerfile installs the pinned real dependencies from `backend/requirements.txt`.

Run the final end-to-end verification on a machine with Docker and internet access:

```bash
cp .env.example .env
docker compose up --build -d
./tests/smoke.sh
make test
make lint
```
