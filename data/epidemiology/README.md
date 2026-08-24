# Institutional epidemiology (source of truth)

Loaded from:

- `diseases.csv` — 50 ICD-10 conditions
- `institutions.csv` — 12 Indian healthcare organizations
- `disease_records.csv` — yearly counts per institution (2015–2026)
- `disease_combinations.csv` — comorbidity cohorts
- `query_results_sample.csv` — independently validated federation totals

**Locality:** each federation agent stores only its assigned institutions.

| Agent | Institutions |
|-------|----------------|
| Hospital A | INST001, 004, 005, 006, 010, 011 |
| Hospital B | INST003, 008, 009 |
| Diagnostic Lab | INST002, 007, 012 |

Reload: `python3 scripts/load_epidemiology.py`

Validated check: Type 2 diabetes mellitus, 2024, all 12 institutions → **6820** (matches Q001).
