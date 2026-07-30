# Deployment

## Production checklist

1. Set `APP_ENV=production`.
2. Generate independent `SECRET_KEY`, `ENCRYPTION_KEY`, database password, and Grafana password.
3. Put the application behind HTTPS and set one canonical `PUBLIC_BASE_URL`, `FRONTEND_URL`, and CORS origin.
4. Place `fullchain.pem` and `privkey.pem` in `nginx/certs/`, then use the complete TLS override:

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
   ```

   This uses `nginx/nginx.tls.conf`, enables TLS 1.2/1.3, HSTS, WebSocket proxying, and HTTP-to-HTTPS redirection.
5. Keep Twilio signature verification enabled and restrict the public webhook surface at the network edge where possible.
6. Use a managed PostgreSQL service with encrypted backups and point-in-time recovery.
7. Use an authenticated, encrypted Redis deployment. Separate Celery broker/result databases as configured.
8. Move application secrets to the deployment platform’s secret manager rather than committing `.env`.
9. Configure SMTP, Twilio, OpenAI, and the OAuth providers required by the organisation.
10. Define recording disclosure, consent, retention, deletion, and do-not-call policies.
11. Alert on API 5xx rate, latency, failed webhooks, failed notifications, worker availability, database storage, and voice-provider errors.

## Scaling

- Run multiple backend replicas behind the reverse proxy. WebSocket connections remain on one replica for the life of a call.
- Increase Celery workers independently for summaries, notifications, and webhook delivery.
- Keep durable state in PostgreSQL and Redis. No voice-call state depends on local process memory.
- For large knowledge bases, replace the JSON embedding scan with pgvector or a managed vector index while keeping the service interface.

## Backups

Back up PostgreSQL and any recordings retained outside Twilio. Redis data is operational rather than authoritative, but AOF is enabled for local resilience. Test restoration regularly.


## Provider callbacks

Set every OAuth provider callback to `https://YOUR_HOST/api/v1/integrations/{provider}/callback`. Twilio voice, status, recording, and Media Stream URLs are derived from the same canonical `PUBLIC_BASE_URL`; do not place a second public proxy URL in front without updating this setting.
