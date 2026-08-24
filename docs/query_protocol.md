# Secure query protocol

Coordinator → `POST /query` on each node:

```json
{
  "query_id": "uuid",
  "schema_version": "1.0",
  "canonical_conditions": {
    "condition": "Type 2 Diabetes",
    "medication": "Metformin",
    "lab": {"code": "4548-4", "operator": ">", "value": 8}
  },
  "privacy_policy": {"k": 10, "differential_privacy": true, "epsilon": 1.0}
}
```

Response: `{count, k_suppressed, dp_applied, schema_version, latency_ms}` only.  
`requested_fields` containing identifiers → HTTP 403.
