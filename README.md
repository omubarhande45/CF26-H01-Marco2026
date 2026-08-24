# CF26-H01-Marco2026

# Federated Clinical Query Fabric (FCQF)

**We don't move healthcare data to the query; we move the query to the healthcare data.**

Privacy-preserving federated analytics across Hospital A, Hospital B, and a Diagnostic Laboratory. Raw patient records never leave a node. Every result carries authorization, privacy validation, provenance, node coverage, and an explicit COMPLETE / PARTIAL / SUPPRESSED / FAILED status.

## Phase 11
Production hardening: policy engine, Laplace DP + budget, OIDC-ready auth, secure query protocol, retries/PARTIAL completeness, security review, expanded tests, dashboard privacy/demo modes. See `PHASE11_IMPLEMENTATION.md` and `docs/`.

## Phases implemented

1. Requirements & architecture — `docs/phase1_architecture.md`, `PHASES.md`
2. Institutional nodes — three SQLite databases, three FastAPI local-query APIs
3. Canonical clinical model + schema mappings — `schema_mapper/mappings.py`
4. Federated query engine — parallel plan/execute/aggregate in `gateway/app.py`
5. Auth & privacy — JWT, RBAC, minimum cohort k=10
6. Provenance & audit — signed digest + SQLite audit trail
7. Fault tolerance — timeouts, OFFLINE/TIMEOUT, PARTIAL results
8. Dashboard — React query builder, federation monitor, audit
9. Tests & benchmark — `tests/`
10. Deployment — `docker-compose.yml` + local process runner

## Demo accounts

| User | Password | Role |
|------|----------|------|
| researcher | research123 | run queries |
| auditor | audit123 | audit + provenance |
| steward | steward123 | node ops |
| admin | admin123 | all |

## Deploy (Vercel UI + separate gateway)

The React app on Vercel is **static**. Login calls `/api/auth/login`. That path only exists if you:

1. Deploy the FastAPI gateway (and nodes) on Railway, Render, Fly.io, or a VPS — **not** on Vercel.
2. In the Vercel project: **Settings → Environment Variables**
   - `GATEWAY_URL` = public gateway URL, e.g. `https://fcqf-gateway.up.railway.app` (no trailing slash)
3. Redeploy. Serverless `api/[...path]` proxies `/api/*` to that gateway.
4. On the gateway, set `ALLOWED_ORIGINS` to include `https://your-app.vercel.app` if you ever call the gateway directly.

Without `GATEWAY_URL`, sign-in shows a clear configuration error instead of a raw Vercel 404.

Local demo still uses Vite proxy → `http://127.0.0.1:8080` (`VITE_API_BASE_URL=/api`).

## Run locally

```bash
python3 institutional_nodes/generate_data.py
# then start nodes + gateway + frontend (see scripts/start_all.sh)
```

Demo query: patients 40–70, Type 2 Diabetes, Metformin, HbA1c > 8, last 12 months.

Stop one node and re-run — status becomes **PARTIAL / completeness NOT GUARANTEED**.
