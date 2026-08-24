# Security

- JWT via `AuthenticationProvider` (`LocalJWTProvider`, stub `OIDCProvider`).
- Secrets from environment (`JWT_SECRET`). Production refuses default secrets.
- RBAC: researcher/clinician query; auditor audit-only.
- CORS allow-list; rate limit 180 req/min/IP.
- Parameterized numeric predicates; terminology allow-lists for IN-lists.
- Forbidden raw fields rejected by policy **and** nodes.
- Generic 500s in `FCQF_ENV=production`.
- `.env.example` contains placeholders only.
