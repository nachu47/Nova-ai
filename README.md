<div align="center">
  <img src="https://img.shields.io/badge/Khair%20IT%20Solution-AI%20Calling%20Assistant-2C3E50?style=for-the-badge&logo=openai" alt="Khair IT Solution Logo" />
  
  <br/>
  
  <h1>Khair IT Solution - AI Calling Assistant</h1>

  <p>
    <strong>A next-generation, production-ready AI voice calling platform.</strong><br/>
    <i>FastAPI Backend • React SaaS Dashboard • Twilio Media Streams • OpenAI Realtime</i>
  </p>

  <p>
    <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React" />
    <img src="https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis" />
    <img src="https://img.shields.io/badge/Twilio-F22F46?style=flat-square&logo=twilio&logoColor=white" alt="Twilio" />
    <img src="https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI" />
  </p>
</div>

<hr />

## Overview

Welcome to the **Khair IT Solution AI Calling Assistant**. This platform is a powerful, multi-tenant AI voice calling solution built for businesses to automate customer interactions using real-time conversational AI. 

Whether you're handling inbound support calls or executing outbound sales campaigns, the AI Assistant can talk naturally, understand context, and seamlessly integrate with your CRM.

---

## Included Capabilities

### Voice & AI Intelligence
- **Inbound & Outbound Twilio Calls**: Native integration with Twilio.
- **Ultra-low Latency**: Bidirectional Twilio Media Streams over WebSockets combined with OpenAI Realtime G.711 μ-law streaming.
- **Natural Interruptions**: Advanced voice activity detection allows callers to seamlessly interrupt the AI.
- **Realtime Transcripts & Memory**: Conversation memory persists across calls using semantic RAG search and auto-generated summaries.
- **Function Calling**: AI can autonomously search knowledge bases, lookup contacts, and book meetings.

### Enterprise Platform
- **Multi-Tenant CRM**: Manage contacts, companies, deals, notes, and tasks natively.
- **Secure Authentication**: Role-based access control (RBAC), rotating JWT refresh tokens, and scoped API keys.
- **Smart Scheduling**: Timezone-aware availability for seamless AI meeting bookings.
- **Advanced Integrations**: Connects to Google Workspace, Microsoft 365, Slack, HubSpot, and Salesforce.
- **Actionable Analytics**: Comprehensive dashboards tracking success rates, durations, revenue, and daily metrics.

### Operations & Security
- **Rock-Solid Infrastructure**: PostgreSQL with Celery work queues and Redis rate-limiting.
- **Enterprise Security**: Argon2id password hashing, Fernet-encrypted OAuth secrets, CSRF protection, and NGINX rate limits.
- **Observability**: Built-in Prometheus metrics and pre-provisioned Grafana dashboards.

---

## Quick Start Guide

You can launch the entire platform in just two commands! Out of the box, it runs in **Local Mock Mode**, allowing you to test the dashboard, CRM, and analytics without needing any paid credentials.

```bash
# 1. Copy the environment template
cp .env.example .env

# 2. Build and start all services
docker compose up --build
```

### Local Services
Once the containers are running, access the platform at these URLs:
| Service | URL |
|---------|-----|
| **Application Dashboard** | [http://localhost](http://localhost) |
| **API Documentation** | [http://localhost/api/v1/docs](http://localhost/api/v1/docs) |
| **Prometheus Metrics** | [http://localhost:9090](http://localhost:9090) |
| **Grafana Dashboards** | [http://localhost:3001](http://localhost:3001) |

> **Default Admin Login:**
> - **Email:** `admin@nova.example.com`
> - **Password:** `NovaAdmin123!`

---

## Enabling Real AI Phone Calls

Ready to connect your AI to real phone numbers? Follow these steps to enable Twilio and OpenAI:

1. **Set up your environment variables** in `.env`:
   ```dotenv
   APP_ENV=production
   PUBLIC_BASE_URL=https://your-domain.ngrok-free.dev
   FRONTEND_URL=https://your-domain.ngrok-free.dev
   CORS_ORIGINS=https://your-domain.ngrok-free.dev
   
   VOICE_PROVIDER_MODE=twilio
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   OPENAI_API_KEY=sk-your-openai-key
   ```

2. **Configure your Twilio Webhook**:
   In your Twilio Phone Number settings, set the **Incoming Call Webhook** to:
   ```text
   POST https://your-domain.ngrok-free.dev/api/v1/voice/twilio/inbound/{agent_id}
   ```
   *(You can find your `agent_id` in the Agents page of the dashboard).*

3. **Restart the backend** to apply the changes:
   ```bash
   docker compose restart backend
   ```

---


## Repository Structure

```bash
Khair IT Solution
 ┣ backend/         # FastAPI, SQLAlchemy schemas, Celery workers
 ┣ frontend/        # React, TypeScript, Vite, Tailwind UI
 ┣ docker/          # Prometheus & Grafana configurations
 ┣ nginx/           # Reverse proxy & WebSocket routing
 ┣ docs/            # Architecture & API documentation
 ┣ scripts/         # Automated setup & utility scripts
 ┣ tests/           # Smoke tests and CI validations
 ┗ docker-compose.yml
```

---

## Common Commands

Managing your deployment is easy with the included Makefile:

```bash
make up                 # Build and start all services
make logs               # Follow all service logs
make test               # Run backend and frontend tests
make lint               # Run Ruff and ESLint formatting
make migrate            # Apply database migrations
make clean              # Remove services and local volumes
./tests/smoke.sh        # Verify a running deployment
```

---

## Documentation
Dive deeper into the platform's architecture and capabilities:

- [Installation Guide](docs/installation.md)
- [Architecture Overview](docs/architecture.md)
- [Database Model](docs/database.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Security Model](docs/security.md)
  
---

<div align="center">
  <p>Built with ❤️ by Khair IT Solution.</p>
</div>
