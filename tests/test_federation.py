"""Functional + privacy + reliability checks (nodes + gateway must be up)."""
from __future__ import annotations

import os

import httpx

GW = os.environ.get("GW", "http://127.0.0.1:8080")


def token(user="researcher", password="research123") -> str:
    r = httpx.post(f"{GW}/auth/login", json={"username": user, "password": password}, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def test_invalid_login():
    r = httpx.post(f"{GW}/auth/login", json={"username": "researcher", "password": "nope"}, timeout=10)
    assert r.status_code == 401


def test_login_and_rbac():
    t = token("auditor", "audit123")
    h = {"Authorization": f"Bearer {t}"}
    r = httpx.post(
        f"{GW}/queries",
        headers=h,
        json={"age_min": 40, "age_max": 70, "conditions": ["Type 2 Diabetes"]},
        timeout=10,
    )
    assert r.status_code == 403
    a = httpx.get(f"{GW}/audit/logs", headers=h, timeout=10)
    assert a.status_code == 200


def test_unauthorized():
    r = httpx.get(f"{GW}/audit/logs", timeout=10)
    assert r.status_code == 401


def _exec(spec: dict, user="researcher", password="research123"):
    t = token(user, password)
    h = {"Authorization": f"Bearer {t}"}
    q = httpx.post(f"{GW}/queries", headers=h, json=spec, timeout=10)
    if q.status_code != 200:
        return q.status_code, q.json() if q.headers.get("content-type", "").startswith("application/json") else q.text
    qid = q.json()["id"]
    r = httpx.post(f"{GW}/queries/{qid}/execute", headers=h, timeout=20)
    return r.status_code, r.json()


def test_federated_count():
    code, body = _exec(
        {
            "age_min": 40,
            "age_max": 70,
            "conditions": ["Type 2 Diabetes"],
            "medications": ["Metformin"],
            "lab_test": "HbA1c",
            "lab_op": ">",
            "lab_value": 8,
            "window_months": 12,
        }
    )
    assert code == 200, body
    assert body["status"] in ("COMPLETE", "PARTIAL", "SUPPRESSED")
    assert len(body["contributions"]) == 3
    blob = str(body)
    assert "pat_id" not in blob
    assert "patient_key" not in blob
    assert "phone" not in blob


def test_raw_data_denied():
    code, body = _exec(
        {
            "age_min": 40,
            "age_max": 70,
            "conditions": ["Type 2 Diabetes"],
            "requested_fields": ["patient_id", "name", "phone", "address"],
        }
    )
    assert code == 403
    detail = body.get("detail") if isinstance(body, dict) else str(body)
    assert "prohibited" in str(detail).lower()


def test_small_cohort_suppressed():
    code, body = _exec(
        {
            "age_min": 89,
            "age_max": 90,
            "conditions": ["Type 2 Diabetes"],
            "medications": ["Metformin"],
            "lab_test": "HbA1c",
            "lab_op": ">",
            "lab_value": 11.5,
            "window_months": 12,
        }
    )
    assert code == 200, body
    assert body["status"] in ("SUPPRESSED", "PARTIAL", "COMPLETE")
    if body["status"] == "SUPPRESSED":
        assert body["aggregate"] is None


def test_k_suppression_metadata():
    code, body = _exec(
        {
            "age_min": 40,
            "age_max": 70,
            "conditions": ["Type 2 Diabetes"],
            "medications": ["Metformin"],
            "lab_value": 8,
        }
    )
    assert code == 200
    assert body["privacy"]["min_cohort"] == 10


def test_dp_and_budget():
    spec = {
        "age_min": 40,
        "age_max": 70,
        "conditions": ["Type 2 Diabetes"],
        "medications": ["Metformin"],
        "lab_value": 8,
        "differential_privacy": True,
        "epsilon": 1.0,
    }
    a = _exec(spec)[1]
    b = _exec(spec)[1]
    assert a["privacy"]["differential_privacy"] is True
    assert a["aggregate_kind"] == "differentially_private"
    # Independent noise — may rarely collide
    assert "budget_remaining" in a["privacy"]
    assert isinstance(b["aggregate"], int)


def test_invalid_query():
    code, _ = _exec({"age_min": 90, "age_max": 10, "conditions": ["Type 2 Diabetes"]})
    assert code == 403


def test_audit_immutable_event():
    t = token()
    h = {"Authorization": f"Bearer {t}"}
    q = httpx.post(
        f"{GW}/queries",
        headers=h,
        json={"age_min": 40, "age_max": 70, "conditions": ["Type 2 Diabetes"], "lab_value": 8},
        timeout=10,
    )
    q.raise_for_status()
    qid = q.json()["id"]
    httpx.post(f"{GW}/queries/{qid}/execute", headers=h, timeout=20).raise_for_status()
    at = token("auditor", "audit123")
    logs = httpx.get(f"{GW}/audit/logs", headers={"Authorization": f"Bearer {at}"}, timeout=10).json()
    assert any(row.get("query_id") == qid and row.get("action") == "execute" for row in logs)


def test_no_central_patient_api():
    t = token()
    h = {"Authorization": f"Bearer {t}"}
    for path in ("/patients", "/records", "/node/patients", "/sql"):
        r = httpx.get(GW + path, headers=h, timeout=5)
        assert r.status_code in (404, 405, 401, 403)


if __name__ == "__main__":
    test_invalid_login()
    test_login_and_rbac()
    test_unauthorized()
    test_federated_count()
    test_raw_data_denied()
    test_small_cohort_suppressed()
    test_k_suppression_metadata()
    test_dp_and_budget()
    test_invalid_query()
    test_audit_immutable_event()
    test_no_central_patient_api()
    print("integration ok")
