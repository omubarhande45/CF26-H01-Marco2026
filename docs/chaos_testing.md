# Chaos testing

| Scenario | Expected |
|----------|----------|
| Node offline | PARTIAL, never COMPLETE |
| Timeout | TIMEOUT contribution, PARTIAL |
| Slow node (`FORCE_SLOW`) | latency recorded or TIMEOUT |
| Malformed (`FORCE_MALFORMED`) | protocol violation ERROR |
| Schema mismatch (`FORCE_INCOMPATIBLE`) | not executed, PARTIAL |
| Auth failure | 401 at agent |
| Policy denial | 403, DENIED |
| Cancel | 409 on execute, not COMPLETE |
