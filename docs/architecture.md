# Architecture

## Container topology

```mermaid
flowchart LR
    Browser[React browser client] --> NGINX[NGINX reverse proxy]
    Twilio[Twilio Voice and Media Streams] --> NGINX
    NGINX --> Frontend[React static container]
    NGINX --> API[FastAPI API and WebSockets]
    API --> PostgreSQL[(PostgreSQL)]
    API --> Redis[(Redis)]
    API <--> OpenAI[OpenAI Realtime and REST]
    API --> Providers[Google / Microsoft / Slack / HubSpot / Salesforce]
    API --> Celery[Celery workers]
    Celery --> Redis
    Celery --> PostgreSQL
    Prometheus --> API
    Grafana --> Prometheus
```

## Voice call sequence

```mermaid
sequenceDiagram
    participant Caller
    participant Twilio
    participant Nova as Nova FastAPI
    participant Realtime as OpenAI Realtime
    participant DB as PostgreSQL

    Caller->>Twilio: Telephone audio
    Twilio->>Nova: Signed voice webhook
    Nova-->>Twilio: TwiML Connect Stream
    Twilio->>Nova: WebSocket start + G.711 media
    Nova->>Realtime: input_audio_buffer.append
    Realtime-->>Nova: response.output_audio.delta
    Nova-->>Twilio: media payload
    Realtime-->>Nova: speech started
    Nova-->>Twilio: clear buffered audio
    Realtime-->>Nova: transcripts and function calls
    Nova->>DB: transcripts, tools, CRM and meetings
    Twilio->>Nova: completion and recording callbacks
    Nova->>DB: duration, recording and outcome
    Nova->>Celery: summarise call
```

## Design decisions

- Synchronous SQLAlchemy sessions keep the transactional model simple and work well with FastAPI’s threadpool for normal API traffic.
- Voice streaming is asynchronous and uses short-lived database sessions for durable events and transcripts.
- Every business record carries an organisation boundary. Route dependencies enforce the boundary before reading or changing a record.
- Refresh tokens are rotated and stored as hashes. Reuse of a rotated token revokes the full token family.
- Provider credentials, OAuth tokens, and webhook secrets are encrypted at rest; outbound webhook and push targets are checked against production SSRF policy.
- The local voice and embedding implementations are deterministic operational modes, not dead code. They make the complete application testable without external accounts.
