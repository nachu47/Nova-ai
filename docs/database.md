# Database model

```mermaid
erDiagram
  ORGANIZATIONS ||--o{ USERS : contains
  ORGANIZATIONS ||--o{ VOICE_AGENTS : owns
  ORGANIZATIONS ||--o{ CONTACTS : owns
  ORGANIZATIONS ||--o{ COMPANIES : owns
  COMPANIES ||--o{ CONTACTS : employs
  CONTACTS ||--o{ CALLS : participates
  VOICE_AGENTS ||--o{ CALLS : handles
  CALLS ||--o{ TRANSCRIPTS : contains
  CALLS ||--|| CALL_SUMMARIES : produces
  CONTACTS ||--o{ DEALS : relates
  CONTACTS ||--o{ MEETINGS : attends
  KNOWLEDGE_DOCUMENTS ||--o{ KNOWLEDGE_CHUNKS : splits
  ORGANIZATIONS ||--o{ INTEGRATIONS : connects
  ORGANIZATIONS ||--o{ WEBHOOK_ENDPOINTS : configures
  WEBHOOK_ENDPOINTS ||--o{ WEBHOOK_DELIVERIES : records
  ORGANIZATIONS ||--o{ USAGE_RECORDS : bills
```

## Tables

The initial Alembic migration creates organisations, users, refresh tokens, one-time tokens, API keys, prompts, voice agents, companies, contacts, deals, CRM notes, CRM tasks, activities, calls, call events, transcripts, call summaries, meetings, knowledge documents, knowledge chunks, integrations, webhook endpoints, webhook deliveries, notifications, usage records, system settings, and audit logs.

Identifiers are UUID strings. Business tables use `created_at`, `updated_at`, and where appropriate `deleted_at`. Foreign keys define cascade, restrict, or set-null behaviour explicitly. High-volume access paths include organisation, status, phone, email, call start, meeting time, usage period, transcript sequence, and audit request indexes.
