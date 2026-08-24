# Differential privacy

Mechanism: Laplace, sensitivity 1 (distinct-patient count).  
Noise scale `b = 1/ε`. Released value is `max(0, round(count + Lap(b)))`.

- Applied **after** k-suppression.
- Never applied to raw records.
- Each execution consumes ε from the actor’s per-institution budget (default 8.0).
- Repeated identical queries consume budget again and receive independent noise (blocks trivial averaging without cost).
