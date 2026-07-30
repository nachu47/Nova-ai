# Nova AI Calling Assistant

Nova is a production-oriented, multi-tenant AI voice calling platform with a FastAPI backend, React SaaS dashboard, PostgreSQL, Redis, Celery, Twilio Media Streams, OpenAI Realtime, CRM, scheduling, RAG, integrations, notifications, analytics, monitoring, and administration.

The repository starts immediately in **local mock voice mode**. Mock mode exercises authentication, agents, CRM, outbound-call creation, transcripts, summaries, analytics, webhooks, and the complete dashboard without paid credentials. Set `VOICE_PROVIDER_MODE=twilio` and add Twilio/OpenAI credentials to use real telephone calls and realtime speech.

## Start the complete platform

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Application: `http://localhost`
- Swagger API: `http://localhost/api/v1/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

Local administrator:

```text
Email: admin@nova.example.com
Password: NovaAdmin123!
```

Change all local credentials and generated secrets before an internet-facing deployment.

## Included capabilities

### Voice and AI

- Inbound and outbound Twilio calls
- Bidirectional Twilio Media Streams over WebSockets
- OpenAI Realtime G.711 μ-law streaming
- Server-side voice activity and silence detection
- Natural interruptions with Twilio `clear` messages
- Realtime caller and assistant transcripts
- Conversation memory from recent linked-call summaries
- Prompt versioning and agent-specific system prompts
- Function calling for knowledge search, contact lookup, CRM tasks, and meeting booking
- Call recording callbacks, outcomes, sentiment, summaries, and action items
- OpenAI embeddings in production and deterministic local embeddings in demo mode
- Chunking and semantic RAG search

### Platform

- Registration, login, access JWTs, rotating refresh-token families, logout
- Email verification, forgot password, and reset password
- Owner, administrator, member, and viewer RBAC
- Enforced read/write scoped, one-time-visible API keys
- Multi-tenant CRM: contacts, companies, deals, notes, tasks, activities
- Timezone-aware availability, booking, cancellation, and rescheduling
- OAuth connections for Google Workspace, Microsoft 365/Outlook, Slack, HubSpot, and Salesforce
- Email, SMS, WhatsApp, and HTTP push notifications
- Signed outbound webhooks with SSRF checks, retries, and delivery records
- Daily/monthly analytics, success rate, duration, revenue, and top customers
- User, call, agent, API-key, usage, system-setting, and audit administration

### Operations and security

- PostgreSQL relational schema with foreign keys, indexes, constraints, soft deletion, and audit logs
- Redis-backed rate limits and Celery work queues
- Argon2id password hashing
- Encrypted OAuth and webhook secrets using Fernet
- CSRF protection for cookie-authenticated token refresh
- CORS allowlist, request validation, parameterised SQLAlchemy queries, security headers, and NGINX limits
- Structured JSON logging in production
- Prometheus metrics and provisioned Grafana dashboard
- Container health checks, persistent volumes, isolated bridge network, and non-root backend process
- Pytest, Vitest, ESLint, Ruff, and GitHub Actions

## Repository structure

```text
backend/                 FastAPI API, SQLAlchemy schema, services, workers, tests
frontend/                React, TypeScript, Vite, Tailwind and shadcn-style UI
docker/                  Prometheus and Grafana configuration
nginx/                   Public reverse proxy and WebSocket routing
docs/                    Architecture, database, API, installation and deployment guides
scripts/                 Secret generation and static checks
tests/                   Deployment smoke test documentation and script
.github/workflows/       Automated backend, frontend and Docker CI
```

A full generated listing is available in `REPOSITORY_TREE.txt`.

## Real Twilio/OpenAI calling

1. Generate strong secrets:

   ```bash
   python scripts/generate_secrets.py
   ```

2. Set at least these values in `.env`:

   ```dotenv
   APP_ENV=production
   PUBLIC_BASE_URL=https://voice.example.com
   FRONTEND_URL=https://voice.example.com
   CORS_ORIGINS=https://voice.example.com
   VOICE_PROVIDER_MODE=twilio
   TWILIO_ACCOUNT_SID=...
   TWILIO_AUTH_TOKEN=...
   TWILIO_PHONE_NUMBER=+...
   OPENAI_API_KEY=...
   ```

3. Put TLS certificates at `nginx/certs/fullchain.pem` and `nginx/certs/privkey.pem`, then start with the supplied TLS override:

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
   ```
4. In Twilio, configure the phone number’s incoming voice webhook as:

   ```text
   POST https://voice.example.com/api/v1/voice/twilio/inbound/{agent_id}
   ```

5. Keep Twilio signature validation enabled. The generated TwiML establishes a bidirectional `<Connect><Stream>` session to the signed Nova WebSocket endpoint.

Phone-call consent, recording notices, do-not-call obligations, emergency-call restrictions, data retention, and AI disclosure requirements vary by jurisdiction. Configure scripts and operating policies with qualified legal review before calling real people.

## Common commands

```bash
make up                 # build and start
make logs               # follow all service logs
make test               # backend and frontend tests in containers
make lint               # Ruff and ESLint
make migrate            # apply Alembic migrations
make clean               # remove services and local volumes
./tests/smoke.sh        # verify a running deployment
```

## API authentication

For browser sessions, send the access token as `Authorization: Bearer ...`. Refresh uses the HTTP-only `nova_refresh` cookie plus `X-CSRF-Token`, which must match the `nova_csrf` cookie.

For server-to-server access, create an API key in Settings and send:

```http
X-API-Key: nova_ab12cd34.secret-value
```

The API key is returned once. Only its SHA-256 hash is stored.

## Documentation

- [Installation guide](docs/installation.md)
- [Architecture](docs/architecture.md)
- [Database model](docs/database.md)
- [API guide](docs/api.md)
- [Deployment guide](docs/deployment.md)
- [Security model](docs/security.md)

## Licence

MIT. See `LICENSE`.
