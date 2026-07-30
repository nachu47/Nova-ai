# API guide

Interactive Swagger documentation is served at `/api/v1/docs`; OpenAPI JSON is at `/api/v1/openapi.json`.

## Authentication example

```bash
TOKEN=$(curl -s http://localhost/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@nova.example.com","password":"NovaAdmin123!"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -s http://localhost/api/v1/agents \
  -H "Authorization: Bearer $TOKEN"
```

## Create an agent

```bash
curl -X POST http://localhost/api/v1/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"Support Agent",
    "description":"First-line customer support",
    "system_prompt":"You are a professional support assistant. Confirm key details, use the knowledge base, and create a follow-up task when required.",
    "greeting":"Hello, this is Nova support. How may I help?"
  }'
```

## Main route groups

- `/auth`: registration, login, refresh, logout, verification, password reset, profile
- `/users`: profile and API keys
- `/agents`: voice-agent lifecycle
- `/calls`: outbound calls, history, transcripts, summaries, mock simulation
- `/voice`: Twilio inbound, TwiML, status, recording, and Media Stream endpoints
- `/crm`: contacts, companies, deals, notes, tasks, timeline
- `/scheduling`: availability and meeting lifecycle
- `/ai`: prompts, knowledge ingestion and semantic search
- `/integrations`: OAuth and allowlisted provider requests
- `/webhooks`: endpoint and delivery management
- `/notifications`: email, SMS, WhatsApp, and push delivery
- `/analytics`: dashboard, daily/monthly series, and top customers
- `/admin`: users, calls, agents, API keys, usage, settings, platform and audits

## Webhook verification

Nova serialises the event body once and signs the exact bytes with HMAC-SHA256. Verify `X-Nova-Signature`, whose format is `sha256=<hex digest>`, using the signing secret returned when the endpoint is created.
