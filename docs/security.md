# Security model

- Passwords use Argon2id with explicit memory, time, and parallelism costs.
- Access JWTs expire after 15 minutes by default. Refresh JWTs are HTTP-only cookies, represented in the database only by SHA-256 hashes, and rotated on use.
- Refresh requests require a matching readable CSRF cookie and `X-CSRF-Token` header.
- RBAC distinguishes owner, administrator, member, and viewer operations.
- API keys have prefixes for lookup, are shown once, and are stored as hashes.
- Organisation identifiers are taken from the authenticated principal, never trusted from normal request bodies.
- SQLAlchemy compiles bound parameters, and Pydantic validates request structures and limits.
- OAuth tokens, webhook signing secrets, and secret system settings are encrypted using a dedicated Fernet key.
- Provider proxy calls enforce an HTTP-method set and provider-specific hostname allowlist to prevent SSRF.
- NGINX and FastAPI apply rate limiting, body limits, CORS policy, request IDs, and security headers.
- Twilio webhook signatures and short-lived signed voice-stream tokens protect the telephony surface.
- Audit rows record actor, organisation, entity, action, request ID, address, agent, and selected before/after data.

For production, store encryption and JWT keys in a secret manager, rotate them under a documented procedure, use managed database encryption and backups, ship logs to a protected central system, and complete threat modelling and penetration testing for the deployed environment.
