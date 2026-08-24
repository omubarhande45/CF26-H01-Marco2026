# Phase 13 — Real-World Federation Simulation

Logical architecture: Dashboard → Gateway/Auth → Coordinator → Federation Agents → local DBs only.

Added: agent metadata/schema versions, per-institution policies, HMAC service auth (mTLS stub), tracing IDs, lifecycle SM, cancel + async execute, planner/explain, onboarding APIs, Research Institute schema, metrics, chaos flags, threat model, prod compose simulation.

Not a hosted production healthcare network — a local multi-agent simulation.
