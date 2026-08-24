# Failure handling

Per-node statuses: `OK`, `TIMEOUT`, `OFFLINE`, `ERROR` (plus health `AVAILABLE` / `DEGRADED`).

Coordinator:

- Concurrent execution
- Per-node timeout (`NODE_TIMEOUT`)
- Retries with exponential backoff (`NODE_RETRIES`)
- Completeness = 100 * successful / total
- Federation status `PARTIAL` if any node fails while others succeed — never labeled complete
