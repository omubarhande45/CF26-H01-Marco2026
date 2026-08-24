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

## Run locally

```bash
python3 institutional_nodes/generate_data.py
# then start nodes + gateway + frontend (see scripts/start_all.sh)
```

Demo query: patients 40–70, Type 2 Diabetes, Metformin, HbA1c > 8, last 12 months.

Stop one node and re-run — status becomes **PARTIAL / completeness NOT GUARANTEED**.
