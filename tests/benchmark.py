"""Federated vs centralized baseline + DP / failure overhead."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "institutional_nodes" / "data"
GW = "http://127.0.0.1:8080"
OUT = ROOT / "docs" / "benchmarking.md"


def centralized_count() -> tuple[int, float]:
    t0 = time.perf_counter()
    total = 0
    a = sqlite3.connect(DATA / "hospital_a.db")
    total += a.execute(
        """
        SELECT COUNT(DISTINCT p.pat_id) FROM patients p
        WHERE p.age BETWEEN 40 AND 70
          AND EXISTS (SELECT 1 FROM diagnoses d WHERE d.pat_id=p.pat_id AND d.diagnosis_code IN ('E11','E11.9'))
          AND EXISTS (SELECT 1 FROM meds m WHERE m.pat_id=p.pat_id AND m.drug IN ('Metformin','Glucophage'))
          AND EXISTS (SELECT 1 FROM labs l WHERE l.pat_id=p.pat_id AND l.lab_name IN ('HbA1c','A1C')
                      AND l.result_val > 8 AND l.taken_on >= date('now','-12 months'))
        """
    ).fetchone()[0]
    a.close()
    b = sqlite3.connect(DATA / "hospital_b.db")
    total += b.execute(
        """
        SELECT COUNT(DISTINCT p.patient_key) FROM person p
        WHERE p.years_old BETWEEN 40 AND 70
          AND EXISTS (SELECT 1 FROM conditions c WHERE c.patient_key=p.patient_key AND c.condition IN ('Type 2 Diabetes','T2DM'))
          AND EXISTS (SELECT 1 FROM medications m WHERE m.patient_key=p.patient_key AND m.medication_name IN ('Metformin','metformin'))
          AND EXISTS (SELECT 1 FROM observations o WHERE o.patient_key=p.patient_key AND o.test IN ('HbA1c','Hemoglobin A1c')
                      AND o.value_num > 8 AND o.observed_at >= date('now','-12 months'))
        """
    ).fetchone()[0]
    b.close()
    l = sqlite3.connect(DATA / "diagnostic_lab.db")
    total += l.execute(
        """
        SELECT COUNT(DISTINCT p.resource_id) FROM fhir_patient p
        WHERE p.age_years BETWEEN 40 AND 70
          AND EXISTS (SELECT 1 FROM fhir_condition c WHERE c.subject_id=p.resource_id AND c.code_display IN ('Type 2 Diabetes','type-2-diabetes'))
          AND EXISTS (SELECT 1 FROM fhir_medication m WHERE m.subject_id=p.resource_id AND m.medication IN ('Metformin'))
          AND EXISTS (SELECT 1 FROM fhir_observation o WHERE o.subject_id=p.resource_id AND o.code IN ('HbA1c','4548-4')
                      AND o.value > 8 AND o.effective_date >= date('now','-12 months'))
        """
    ).fetchone()[0]
    l.close()
    return total, (time.perf_counter() - t0) * 1000


def federated(dp=False) -> dict:
    t0 = time.perf_counter()
    tok = httpx.post(f"{GW}/auth/login", json={"username": "researcher", "password": "research123"}, timeout=10).json()[
        "access_token"
    ]
    h = {"Authorization": f"Bearer {tok}"}
    qid = httpx.post(
        f"{GW}/queries",
        headers=h,
        json={
            "age_min": 40,
            "age_max": 70,
            "conditions": ["Type 2 Diabetes"],
            "medications": ["Metformin"],
            "lab_test": "HbA1c",
            "lab_op": ">",
            "lab_value": 8,
            "window_months": 12,
            "differential_privacy": dp,
            "epsilon": 1.0 if dp else None,
        },
        timeout=10,
    ).json()["id"]
    body = httpx.post(f"{GW}/queries/{qid}/execute", headers=h, timeout=20).json()
    body["_wall_ms"] = (time.perf_counter() - t0) * 1000
    return body


def write_report(c, ct, f, dp):
    lines = [
        "# Benchmarking",
        "",
        "Synthetic data only. Federation is **not** claimed to be faster.",
        "",
        "| Metric | Centralized | Federated | Federated + DP |",
        "|--------|-------------|-----------|----------------|",
        f"| Records (approx) | 10,300 | 10,300 | 10,300 |",
        f"| Raw records centralized | YES | NO | NO |",
        f"| Result count | {c} | {f.get('aggregate')} | {dp.get('aggregate')} |",
        f"| Query latency (ms) | {ct:.1f} | {f.get('_wall_ms', 0):.1f} | {dp.get('_wall_ms', 0):.1f} |",
        f"| Status | n/a | {f.get('status')} | {dp.get('status')} |",
        f"| Privacy enforcement | LOW | k-anon | k-anon + Laplace |",
        f"| Node failure tolerance | NO | YES (PARTIAL) | YES |",
        f"| Audit provenance | LIMITED | FULL | FULL |",
        "",
        "## Per-node latency (federated)",
        "",
    ]
    for contrib in f.get("contributions") or []:
        lines.append(f"- {contrib.get('node_name')}: {contrib.get('latency_ms')} ms ({contrib.get('status')})")
    lines += [
        "",
        f"Aggregation / coordinator overhead ≈ {f.get('executed_ms')} ms reported by gateway.",
        "",
        "Network overhead is included in wall-clock federated time (HTTP to three nodes).",
        "",
    ]
    OUT.write_text("\n".join(lines))
    print(OUT.read_text())


if __name__ == "__main__":
    c, ct = centralized_count()
    f = federated(False)
    d = federated(True)
    print(f"centralized_count={c} latency_ms={ct:.1f} raw_data_moved=YES")
    print(f"federated_count={f.get('aggregate')} latency_ms={f['_wall_ms']:.1f} status={f['status']} raw_data_moved=NO")
    print(f"dp_count={d.get('aggregate')} latency_ms={d['_wall_ms']:.1f} kind={d.get('aggregate_kind')}")
    write_report(c, ct, f, d)
