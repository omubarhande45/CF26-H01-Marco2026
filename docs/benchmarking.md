# Benchmarking

Synthetic data only. Federation is **not** claimed to be faster.

| Metric | Centralized | Federated | Federated + DP |
|--------|-------------|-----------|----------------|
| Records (approx) | 10,300 | 10,300 | 10,300 |
| Raw records centralized | YES | NO | NO |
| Result count | 148 | 144 | 142 |
| Query latency (ms) | 277.4 | 233.1 | 194.1 |
| Status | n/a | COMPLETE | COMPLETE |
| Privacy enforcement | LOW | k-anon | k-anon + Laplace |
| Node failure tolerance | NO | YES (PARTIAL) | YES |
| Audit provenance | LIMITED | FULL | FULL |

## Per-node latency (federated)

- Diagnostic Laboratory: 54.09 ms (OK)
- Hospital A: 127.86 ms (OK)
- Hospital B: 112.42 ms (OK)

Aggregation / coordinator overhead ≈ 155.82 ms reported by gateway.

Network overhead is included in wall-clock federated time (HTTP to three nodes).
