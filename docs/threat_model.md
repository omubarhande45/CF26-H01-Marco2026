# Threat model

| Threat | Impact | Mitigation | Status | Future |
|--------|--------|------------|--------|--------|
| Malicious researcher | Row-level extraction | Policy + forbidden fields + RBAC | Implemented | OPA |
| Compromised institution | Bad aggregates | Completeness, PARTIAL, protocol checks | Implemented | Signed attestations |
| Malicious agent | PHI leak in payload | Coordinator rejects `patients`/`name` keys | Implemented | mTLS identity |
| Stolen JWT | Impersonation | 8h expiry, prod secrets | Partial | Short-lived + rotation |
| Replay | Repeat service token | 300s HMAC timestamp | Implemented | Nonces |
| Query inference | Reconstruct counts | k-anon + DP + budget | Implemented | Tighter accountant |
| SQL injection | Data exfil | Allow-listed codes, bound params | Implemented | Prepared IN lists |
| Traffic intercept | Token theft | Dev HTTP | Planned | TLS/mTLS |
| Audit tampering | Cover tracks | Append-only SQLite | Partial | WORM / signatures |
| Privacy budget abuse | Exhaust / over-query | Per-actor ledger | Implemented | Quotas + alerts |
