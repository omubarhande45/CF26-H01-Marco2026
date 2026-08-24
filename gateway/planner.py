"""Safe query plan — no SQL, no PHI."""
from __future__ import annotations

from typing import Any


def plan_query(spec: dict, nodes: list[dict], schema_status: dict[str, str]) -> dict[str, Any]:
    eligible = [n["id"] for n in nodes if schema_status.get(n["id"]) == "COMPATIBLE"]
    mappings = []
    if spec.get("conditions"):
        mappings.append("condition→ICD/named/FHIR/display")
    if spec.get("medications"):
        mappings.append("medication→local formulary")
    if spec.get("lab_value") is not None:
        mappings.append("HbA1c/LOINC 4548-4")
    eps = spec.get("epsilon") if spec.get("differential_privacy") else 0
    return {
        "eligible_nodes": eligible,
        "ineligible_nodes": [n["id"] for n in nodes if n["id"] not in eligible],
        "required_terminology_mappings": mappings,
        "estimated_cost": max(1, len(eligible)),
        "privacy_cost": {"epsilon": eps or 0, "k": 10},
        "expected_response_type": "aggregate_count",
    }


def explain(contribs: list[dict], schema_status: dict[str, str], policy_ok: bool, dp: bool) -> list[dict]:
    out = []
    for c in contribs:
        nid = c.get("node_id")
        reasons = []
        st = schema_status.get(nid, "UNKNOWN")
        if st == "COMPATIBLE":
            reasons.append("Compatible schema")
        elif st == "INCOMPATIBLE":
            reasons.append("Incompatible schema — not executed blindly")
        else:
            reasons.append("Schema compatibility unknown")
        if policy_ok:
            reasons.append("Policy allows aggregate count")
        if c.get("k_suppressed"):
            reasons.append("Result suppressed: cohort < k")
        if c.get("status") in {"OFFLINE", "TIMEOUT", "ERROR"}:
            reasons.append(f"Node {c.get('status').lower()}")
        if c.get("status") == "OK" and not c.get("k_suppressed"):
            reasons.append("Cohort satisfies k threshold")
        if dp and c.get("dp_applied"):
            reasons.append("Differential privacy applied to aggregate")
        out.append({"node_id": nid, "node_name": c.get("node_name"), "status": c.get("status"), "reasons": reasons})
    return out
