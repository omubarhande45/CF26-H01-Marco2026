# Architecture (Phase 11)

Researcher → Dashboard → Gateway (auth provider, policy, planner)  
→ Secure query envelope → Hospital A / Hospital B / Diagnostic Lab  
→ Local SQL **counts only** → k-suppression → optional Laplace DP  
→ Coordinator aggregate → provenance + audit → client

The coordinator never opens institutional SQLite files. Patient tables exist only inside each node process.
