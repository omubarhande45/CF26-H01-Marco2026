# Federated Clinical Query Fabric — Phase Plan

**Pitch:** We don't move healthcare data to the query; we move the query to the healthcare data.

| Phase | Status | Deliverable |
|-------|--------|-------------|
| 1 Requirements & Architecture | Done | Use cases, architecture, query model, metrics |
| 2 Institutional Data Nodes | Done | Hospital A, Hospital B, Diagnostic Lab |
| 3 Canonical Clinical Model | Done | Mappings from heterogeneous schemas |
| 4 Federated Query Engine | Done | Parse, plan, execute, aggregate |
| 5 Authorization & Privacy | Done | JWT, RBAC, minimum cohort k=10 |
| 6 Provenance & Audit | Done | Query lineage + audit log |
| 7 Fault Tolerance | Done | Health, timeout, PARTIAL |
| 8 Dashboard | Done | Query builder, monitor, provenance |
| 9 Testing & Benchmarking | Done | Federated vs centralized baseline |
| 10 Deployment & Demo | Done | Compose + running local stack |
| 11 Hardening & Advanced Privacy | Done | DP, policy, OIDC-ready auth, protocol, tests |
| 13 Federation simulation | Done | Agents, lifecycle, tracing, onboarding, chaos |

## Success metrics
- Zero raw patient records leave a node
- Every result has status COMPLETE | PARTIAL | SUPPRESSED | INVALIDATED
- Minimum cohort k=10 (configurable)
- Explicit node coverage on every result
