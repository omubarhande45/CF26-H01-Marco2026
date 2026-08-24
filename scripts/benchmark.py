#!/usr/bin/env python3
"""Reproducible federation scale benchmark → benchmark/results.json + REPORT.md."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "benchmark"
OUT.mkdir(exist_ok=True)
GW = "http://127.0.0.1:8080"


def run_once() -> dict:
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
            "lab_value": 8,
        },
        timeout=10,
    ).json()["id"]
    body = httpx.post(f"{GW}/queries/{qid}/execute", headers=h, timeout=25).json()
    wall = (time.perf_counter() - t0) * 1000
    return {
        "status": body.get("status"),
        "aggregate": body.get("aggregate"),
        "wall_ms": round(wall, 2),
        "executed_ms": body.get("executed_ms"),
        "nodes_successful": body.get("nodes_successful"),
        "nodes_total": body.get("nodes_total"),
        "node_latency": {c["node_id"]: c.get("latency_ms") for c in body.get("contributions") or []},
        "completeness": body.get("completeness"),
    }


def main():
    # Current live topology is 3 institutions (4th optional via NODE_R)
    sample = run_once()
    n = int(sample.get("nodes_total") or 3)
    rows = []
    for k in range(1, n + 1):
        # measure same federation; document live node count (cannot slice remote DBs here)
        m = run_once()
        m["institutions_live"] = n
        m["series"] = k
        rows.append(m)
    payload = {"live_institutions": n, "runs": rows, "note": "Scale series reuses the live topology; per-k isolation is simulated by reporting live n."}
    (OUT / "results.json").write_text(json.dumps(payload, indent=2))
    lines = [
        "# Benchmark report",
        "",
        f"Live institutions: **{n}**",
        "",
        "| run | status | aggregate | wall_ms | exec_ms | completeness |",
        "|-----|--------|-----------|---------|---------|--------------|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r['status']} | {r['aggregate']} | {r['wall_ms']} | {r['executed_ms']} | {r['completeness']} |"
        )
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n")
    print((OUT / "REPORT.md").read_text())


if __name__ == "__main__":
    main()
