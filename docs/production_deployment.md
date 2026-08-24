# Production vs simulation

`docker-compose.prod.yml` is a **local production-mode simulation**:

- `FCQF_ENV=production`
- strong `JWT_SECRET` required
- demo users **off** unless `ALLOW_DEMO_USERS=1`
- restricted CORS
- `REQUIRE_SERVICE_AUTH=1`

This is not a hosted multi-region healthcare deployment. TLS/mTLS, real OIDC, and managed DBs remain future work.
