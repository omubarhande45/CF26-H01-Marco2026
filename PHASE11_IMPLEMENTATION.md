# Phase 11 — Production Hardening & Advanced Privacy

## Architecture changes
- Auth abstraction: `gateway/auth_providers.py` (`LocalJWTProvider`, `OIDCProvider` stub).
- Policy engine: `privacy/policy.py` (role, fields, k, budget, aggregation, window).
- DP: `privacy/dp.py` Laplace + per-(actor, institution) ε ledger.
- Secure query envelope between coordinator and nodes.
- Node-local audit DBs; coordinator never opens patient SQLite files.
- Retries + completeness percentage; PARTIAL never labeled complete.

## APIs (unchanged paths)
`POST /auth/login`, `POST /queries`, `POST /queries/{id}/execute`, results/provenance/audit/nodes.  
Added `GET /privacy/budget`.

## Limitations
- OIDC is a structural stub (not a live IdP).
- Laplace is not a full (ε,δ)-zCDP accountant.
- In-memory query store and rate limiter (not multi-replica).
- Demo credentials remain for local/hackathon use.

## Future
Live OIDC JWKS, Gaussian mechanism, per-node policy-as-code (OPA), signed attestations.
