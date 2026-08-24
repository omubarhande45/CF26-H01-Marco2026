# Phase 1 — Requirements & Architecture

## Use cases
1. Researcher counts a cohort across Hospital A, Hospital B, and Diagnostic Lab.
2. Auditor reviews who ran which query and which nodes participated.
3. Data steward sees node health and schema versions.
4. Demo: one node offline → PARTIAL result, never a silent total.

## Canonical query model
```
COUNT DISTINCT patients
WHERE age BETWEEN min AND max
  AND gender IN (...)
  AND condition IN (canonical codes)
  AND medication IN (canonical names)
  AND lab_test = HbA1c AND value > threshold
  AND time_window_months = 12
```

## Data-flow boundary
Researcher → Dashboard → Gateway (auth/policy) → Planner
→ Institutional nodes (local SQL only) → Aggregates only
→ Privacy validation → Provenance → Client

## Roles
researcher, clinician, data_steward, auditor, admin
