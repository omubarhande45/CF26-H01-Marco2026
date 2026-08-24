# API integration (implemented)

Base: gateway `:8080`. Browser uses `/api` proxy. Nodes are never called from the browser.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /auth/login | no | JWT |
| GET | /auth/me | JWT | role |
| GET | /config | no | env + demo flag |
| GET | /stats | JWT | dashboard KPIs |
| GET | /nodes | JWT | node health |
| GET | /topology | JWT | federation map |
| GET | /institutions | JWT | registry |
| GET | /institutions/{id} | JWT | profile + health |
| POST | /queries | query role | create |
| GET | /queries | JWT | history |
| GET | /queries/{id} | JWT | lifecycle |
| POST | /queries/{id}/execute | query | sync run |
| POST | /queries/{id}/execute-async | query | async run |
| POST | /queries/{id}/cancel | query | cancel |
| POST | /queries/preview-policy | JWT | policy only |
| GET | /queries/{id}/result | JWT | aggregates |
| GET | /queries/{id}/provenance | JWT | lineage |
| GET | /privacy/budget | JWT | ε remaining |
| GET | /audit/logs | auditor | events |
| GET | /audit/logs/{id} | auditor | event |
| GET | /benchmarks | JWT | results.json |
| GET | /health | no | liveness |
| GET | /metrics | no | prometheus |

Errors: 401 missing/invalid token, 403 policy/RBAC, 404 missing, 409 cancel, 429 rate limit, 503 node down.
