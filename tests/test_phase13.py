"""Phase 13 unit + integration tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.lifecycle import InvalidTransition, advance
from gateway.service_auth import SharedTokenAuthenticator
from gateway.planner import plan_query


def test_lifecycle_rejects_invalid():
    assert advance("CREATED", "VALIDATING") == "VALIDATING"
    try:
        advance("CREATED", "COMPLETED")
        raise AssertionError("should reject")
    except InvalidTransition:
        pass


def test_service_auth_hmac():
    os.environ["SERVICE_TOKEN"] = "unit-secret"
    os.environ["REQUIRE_SERVICE_AUTH"] = "1"
    a = SharedTokenAuthenticator()
    hdrs = a.issue("hospital_a")
    low = {k.lower(): v for k, v in hdrs.items()}
    assert a.verify(low, "hospital_a") is True
    assert a.verify({"x-fcqf-service-token": "nope"}, "hospital_a") is False
    os.environ.pop("REQUIRE_SERVICE_AUTH", None)


def test_planner_eligible():
    p = plan_query(
        {"conditions": ["Type 2 Diabetes"], "lab_value": 8},
        [{"id": "hospital_a"}, {"id": "hospital_b"}],
        {"hospital_a": "COMPATIBLE", "hospital_b": "INCOMPATIBLE"},
    )
    assert p["eligible_nodes"] == ["hospital_a"]
    assert "hospital_b" in p["ineligible_nodes"]


def test_integration_lifecycle_and_trace():
    import httpx

    gw = os.environ.get("GW", "http://127.0.0.1:8080")
    tok = httpx.post(f"{gw}/auth/login", json={"username": "researcher", "password": "research123"}, timeout=10).json()[
        "access_token"
    ]
    h = {"Authorization": f"Bearer {tok}"}
    q = httpx.post(
        f"{gw}/queries",
        headers=h,
        json={"age_min": 40, "age_max": 70, "conditions": ["Type 2 Diabetes"], "medications": ["Metformin"], "lab_value": 8},
        timeout=10,
    )
    assert q.status_code == 200, q.text
    body = q.json()
    assert body.get("trace_id")
    assert body.get("correlation_id")
    qid = body["id"]
    r = httpx.post(f"{gw}/queries/{qid}/execute", headers=h, timeout=20)
    assert r.status_code == 200
    rec = httpx.get(f"{gw}/queries/{qid}", headers=h, timeout=10).json()
    assert rec.get("trace_id")
    assert rec.get("status") in {"COMPLETED", "PARTIAL", "SUPPRESSED", "FAILED"}
    assert "CREATED" in (rec.get("lifecycle") or [])
    ex = httpx.get(f"{gw}/queries/{qid}/explain", headers=h, timeout=10)
    assert ex.status_code == 200
    topo = httpx.get(f"{gw}/topology", headers=h, timeout=10)
    assert topo.status_code == 200
    m = httpx.get(f"{gw}/metrics", timeout=10)
    assert m.status_code == 200
    assert "fcqf_queries_total" in m.text


def test_cancel_created():
    import httpx

    gw = os.environ.get("GW", "http://127.0.0.1:8080")
    tok = httpx.post(f"{gw}/auth/login", json={"username": "researcher", "password": "research123"}, timeout=10).json()[
        "access_token"
    ]
    h = {"Authorization": f"Bearer {tok}"}
    qid = httpx.post(
        f"{gw}/queries",
        headers=h,
        json={"age_min": 40, "age_max": 70, "conditions": ["Type 2 Diabetes"]},
        timeout=10,
    ).json()["id"]
    c = httpx.post(f"{gw}/queries/{qid}/cancel", headers=h, timeout=10)
    assert c.status_code == 200
    assert c.json()["status"] == "CANCELLED"
    bad = httpx.post(f"{gw}/queries/{qid}/execute", headers=h, timeout=10)
    assert bad.status_code == 409


def test_onboarding_admin():
    import httpx

    gw = os.environ.get("GW", "http://127.0.0.1:8080")
    tok = httpx.post(f"{gw}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    listed = httpx.get(f"{gw}/institutions", headers=h, timeout=10)
    assert listed.status_code == 200


if __name__ == "__main__":
    test_lifecycle_rejects_invalid()
    test_service_auth_hmac()
    test_planner_eligible()
    test_integration_lifecycle_and_trace()
    test_cancel_created()
    test_onboarding_admin()
    print("phase13 ok")
