# Privacy model

1. Data locality — raw rows never leave a node.
2. k-anonymity — node counts &lt; 10 are nulled (`k_suppressed`).
3. Optional Laplace DP on released aggregates only.
4. Privacy budget ε per (actor, institution).
5. Policy engine denies row-level / identifier requests.

Aggregate kinds: `exact` | `k_suppressed` | `differentially_private`.
