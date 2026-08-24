"""Full connected flow against a live stack."""
from __future__ import annotations

import os

import httpx

GW = os.environ.get("GW", "http://127.0.0.1:8080")


def test_e2e():
    bad = httpx.post(f"{GW}/auth/login", json={"username": "x", "password": "y"}, timeout=10)
    assert bad.status_code == 401
    tok = httpx.post(f"{GW}/auth/login", json={"username": "researcher", "password": "research123"}, timeout=10)
    tok.raise_for_status()
    h = {"Authorization": f"Bearer {tok.json()['access_token']}"}
    me = httpx.get(f"{GW}/auth/me", headers=h, timeout=10)
    assert me.json()["role"] == "researcher"
    st = httpx.get(f"{GW}/stats", headers=h, timeout=10)
    st.raise_for_status()
    assert st.json()["nodes_total"] >= 3
    spec = {
        "age_min": 40,
        "age_max": 70,
        "conditions": ["Type 2 Diabetes"],
        "medications": ["Metformin"],
        "lab_test": "HbA1c",
        "lab_op": ">",
        "lab_value": 8,
        "window_months": 12,
    }
    q = httpx.post(f"{GW}/queries", headers=h, json=spec, timeout=10)
    q.raise_for_status()
    qid = q.json()["id"]
    assert q.json().get("trace_id")
    r = httpx.post(f"{GW}/queries/{qid}/execute", headers=h, timeout=25)
    r.raise_for_status()
    body = r.json()
    assert body["status"] in ("COMPLETE", "PARTIAL", "SUPPRESSED")
    assert "pat_id" not in str(body)
    lst = httpx.get(f"{GW}/query-history", headers=h, timeout=10)
    lst.raise_for_status()
    assert any(i["id"] == qid for i in lst.json())
    httpx.get(f"{GW}/queries/{qid}/provenance", headers=h, timeout=10).raise_for_status()
    # auditor cannot create
    at = httpx.post(f"{GW}/auth/login", json={"username": "auditor", "password": "audit123"}, timeout=10).json()["access_token"]
    ah = {"Authorization": f"Bearer {at}"}
    assert httpx.post(f"{GW}/queries", headers=ah, json=spec, timeout=10).status_code == 403
    assert httpx.get(f"{GW}/audit/logs", headers=ah, timeout=10).status_code == 200
    for path in ("/patients", "/records", "/raw", "/export"):
        assert httpx.get(GW + path, headers=h, timeout=5).status_code in (404, 401, 403, 405)
    denied = httpx.post(
        f"{GW}/queries",
        headers=h,
        json={**spec, "requested_fields": ["patient_id", "name", "phone", "address"]},
        timeout=10,
    )
    assert denied.status_code == 403


if __name__ == "__main__":
    test_e2e()
    print("e2e ok")
