# Federation architecture (Phase 13)

Researcher → Dashboard → API Gateway/Auth → Federation Coordinator  
→ Federation Agent (Hospital A | Hospital B | Diagnostic Lab | optional Research Institute)  
→ local SQLite only.

The coordinator never opens institutional database files. Agents authenticate service tokens, validate envelopes, map canonical concepts, aggregate locally, apply k/DP, and return counts plus metadata.
