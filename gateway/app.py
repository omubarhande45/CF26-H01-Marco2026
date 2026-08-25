"""FCQF API Gateway: auth, policy, planner, aggregation, DP, provenance, audit."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def _load_dotenv() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)

_load_dotenv()

from gateway.auth_providers import build_provider
from gateway.metrics import inc, observe, render as render_metrics
from gateway.planner import explain as explain_plan
from gateway.planner import plan_query
from gateway.service_auth import build_service_auth
from institutions.profiles import PROFILES, strictest_k
from privacy.dp import DPError, PrivacyBudgetLedger, validate_delta, validate_epsilon
from privacy.policy import evaluate_policy
from shared.lifecycle import InvalidTransition, advance
from shared.models import ClinicalQuery, NodeContribution, QueryResult, ResultStatus
from shared.tracing import new_ids

MIN_COHORT = int(os.environ.get("MIN_COHORT", "10"))
NODE_TIMEOUT = float(os.environ.get("NODE_TIMEOUT", "4.0"))
NODE_RETRIES = int(os.environ.get("NODE_RETRIES", "2"))
DEFAULT_EPSILON = float(os.environ.get("DEFAULT_EPSILON", "1.0"))
DEFAULT_DELTA = float(os.environ.get("DEFAULT_DELTA", "1e-5"))
BUDGET = float(os.environ.get("PRIVACY_BUDGET_PER_ACTOR", "8.0"))
STORE = ROOT / "gateway" / "store"
STORE.mkdir(parents=True, exist_ok=True)
AUDIT_DB = STORE / "control_plane.db"
FCQF_ENV = os.environ.get("FCQF_ENV", "development")

NODES = [
    {"id": "hospital_a", "name": "Hospital A", "url": os.environ.get("NODE_A", "http://127.0.0.1:8101"), "active": True},
    {"id": "hospital_b", "name": "Hospital B", "url": os.environ.get("NODE_B", "http://127.0.0.1:8102"), "active": True},
    {"id": "diagnostic_lab", "name": "Diagnostic Laboratory", "url": os.environ.get("NODE_L", "http://127.0.0.1:8103"), "active": True},
]
if os.environ.get("NODE_R"):
    NODES.append(
        {
            "id": "research_institute",
            "name": "Research Institute",
            "url": os.environ["NODE_R"],
            "active": True,
        }
    )

svc_auth = build_service_auth()
CANONICAL_EXPECTED = "1.0"

ROLE_PERMS = {
    "researcher": {"query", "read_result", "read_provenance", "read_nodes"},
    "clinician": {"query", "read_result", "read_provenance", "read_nodes"},
    "auditor": {"read_result", "read_provenance", "read_audit", "read_nodes"},
    "data_steward": {"read_nodes", "read_result", "read_audit"},
    "admin": {"query", "read_result", "read_provenance", "read_audit", "read_nodes", "admin"},
}

authz = build_provider()
ledger = PrivacyBudgetLedger(default_budget=BUDGET)

_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
if "*" not in _origins:
    _origins = list({*_origins, "*"})

app = FastAPI(title="FCQF Gateway", version="0.11.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.(vercel\.app|railway\.app)",
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=False,
    expose_headers=["*"],
)

QUERIES: dict[str, dict[str, Any]] = {}
_rate: dict[str, deque] = defaultdict(deque)


def _init_store():
    con = sqlite3.connect(AUDIT_DB)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY,
            ts TEXT,
            actor TEXT,
            role TEXT,
            action TEXT,
            query_id TEXT,
            detail TEXT
        );
        CREATE TABLE IF NOT EXISTS provenance (
            id TEXT PRIMARY KEY,
            query_id TEXT,
            payload TEXT,
            created_at TEXT
        );
        """
    )
    con.commit()
    con.close()


_init_store()


def audit(actor: str, role: str, action: str, query_id: str | None, detail: str):
    con = sqlite3.connect(AUDIT_DB)
    con.execute(
        "INSERT INTO audit (ts,actor,role,action,query_id,detail) VALUES (?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), actor, role, action, query_id, detail[:800]),
    )
    con.commit()
    con.close()


class LoginIn(BaseModel):
    username: str
    password: str


class QueryCreate(ClinicalQuery):
    purpose: str = "clinical_research"


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in ("/", "/health", "/docs", "/openapi.json", "/metrics"):
        return await call_next(request)
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _rate[ip]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    limit = 180
    if len(bucket) >= limit:
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
    bucket.append(now)
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    if FCQF_ENV == "production":
        return JSONResponse({"detail": "internal error"}, status_code=500)
    return JSONResponse({"detail": str(exc)}, status_code=500)


def current_user(
    authorization: str | None = Header(default=None),
    x_fcqf_token: str | None = Header(default=None, alias="X-FCQF-Token"),
    fcqf_access: str | None = Cookie(default=None),
) -> dict:
    raw = None
    if authorization and authorization.lower().startswith("bearer "):
        raw = authorization.split(" ", 1)[1].strip()
    elif x_fcqf_token:
        raw = x_fcqf_token.strip()
    elif fcqf_access:
        raw = fcqf_access.strip()
    if not raw:
        raise HTTPException(401, "missing token")
    return authz.authenticate(raw)


def require(*perms: str):
    def dep(user: dict = Depends(current_user)):
        allowed = ROLE_PERMS.get(user.get("role", ""), set())
        if "admin" in allowed:
            return user
        if not any(p in allowed for p in perms):
            raise HTTPException(403, "insufficient privileges")
        return user

    return dep


@app.post("/auth/login")
def login(body: LoginIn):
    try:
        out = authz.login(body.username, body.password)
    except HTTPException:
        audit(body.username, "anonymous", "login_failed", None, "bad credentials")
        raise
    audit(body.username, out["role"], "login", None, "ok")
    resp = JSONResponse(out)
    resp.set_cookie(
        key="fcqf_access",
        value=out["access_token"],
        max_age=8 * 3600,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return resp


@app.get("/nodes")
def list_nodes(user: dict = Depends(require("read_nodes", "query", "read_result"))):
    return [_probe(n) for n in NODES]


@app.get("/nodes/{node_id}/health")
def node_health(node_id: str, user: dict = Depends(require("read_nodes", "query"))):
    n = next((x for x in NODES if x["id"] == node_id), None)
    if not n:
        raise HTTPException(404, "unknown node")
    return _probe(n)


def _probe(n: dict) -> dict:
    t0 = time.perf_counter()
    try:
        r = httpx.get(f"{n['url']}/health", timeout=2.0)
        data = r.json() if r.status_code == 200 else {}
        healthy = r.status_code == 200
        status = data.get("status") or ("AVAILABLE" if healthy else "ERROR")
        if r.status_code == 503:
            status = "OFFLINE"
        return {
            "node_id": n["id"],
            "name": n["name"],
            "healthy": healthy,
            "status": status,
            "schema_version": data.get("schema_version"),
            "patient_count": data.get("patient_count"),
            "k_threshold": data.get("k_threshold"),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "http_status": r.status_code,
        }
    except httpx.TimeoutException:
        return {
            "node_id": n["id"],
            "name": n["name"],
            "healthy": False,
            "status": "TIMEOUT",
            "schema_version": None,
            "patient_count": None,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception:
        return {
            "node_id": n["id"],
            "name": n["name"],
            "healthy": False,
            "status": "OFFLINE",
            "schema_version": None,
            "patient_count": None,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }


@app.post("/queries")
def create_query(q: QueryCreate, user: dict = Depends(require("query"))):
    qid = str(uuid.uuid4())
    spec = q.model_dump()
    remaining = min(ledger.remaining(user["sub"], n["id"]) for n in NODES)
    decision = evaluate_policy(
        role=user["role"],
        spec=spec,
        k_threshold=MIN_COHORT,
        budget_remaining=remaining,
        requested_epsilon=spec.get("epsilon") if spec.get("differential_privacy") else None,
        historical_count=_history_count(user["sub"]),
    )
    ids = new_ids(qid)
    if not decision.allowed:
        inc("fcqf_queries_denied")
        audit(user["sub"], user["role"], "POLICY_DENIED", qid, decision.reason)
        raise HTTPException(403, decision.reason)

    QUERIES[qid] = {
        "id": qid,
        "query_id": qid,
        "status": "CREATED",
        "lifecycle": ["CREATED"],
        "spec": spec,
        "owner": user["sub"],
        "role": user["role"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "provenance_id": None,
        "policy": decision.as_dict(),
        "correlation_id": ids["correlation_id"],
        "trace_id": ids["trace_id"],
        "cancel_requested": False,
        "events": ["QUERY_CREATED", "POLICY_APPROVED"],
    }
    inc("fcqf_queries_total")
    audit(user["sub"], user["role"], "QUERY_CREATED", qid, f"trace={ids['trace_id']}")
    audit(user["sub"], user["role"], "POLICY_APPROVED", qid, "ok")
    return {
        "id": qid,
        "query_id": qid,
        "status": "CREATED",
        "spec": spec,
        "policy": decision.as_dict(),
        "correlation_id": ids["correlation_id"],
        "trace_id": ids["trace_id"],
    }


@app.get("/query-history")
def list_queries(user: dict = Depends(require("query", "read_result"))):
    items = []
    for rec in QUERIES.values():
        res = rec.get("result") or {}
        spec = rec.get("spec") or {}
        items.append(
            {
                "id": rec.get("id"),
                "query_id": rec.get("query_id") or rec.get("id"),
                "owner": rec.get("owner"),
                "role": rec.get("role"),
                "status": rec.get("status"),
                "created_at": rec.get("created_at"),
                "executed_ms": rec.get("executed_ms") or res.get("executed_ms"),
                "completeness": res.get("completeness"),
                "aggregate": res.get("aggregate"),
                "nodes_successful": res.get("nodes_successful"),
                "nodes_total": res.get("nodes_total"),
                "privacy": res.get("privacy") or {},
                "conditions": spec.get("conditions"),
                "medications": spec.get("medications"),
                "differential_privacy": spec.get("differential_privacy"),
            }
        )
    items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return items


@app.get("/queries/{qid}")
def get_query(qid: str, user: dict = Depends(require("query", "read_result"))):
    rec = QUERIES.get(qid)
    if not rec:
        raise HTTPException(404, "query not found")
    return rec


def _history_count(actor: str) -> int:
    con = sqlite3.connect(AUDIT_DB)
    n = con.execute("SELECT COUNT(*) FROM audit WHERE actor=? AND action='execute'", (actor,)).fetchone()[0]
    con.close()
    return int(n)


def _active_nodes() -> list[dict]:
    return [n for n in NODES if n.get("active", True)]


def _set_state(rec: dict, nxt: str):
    rec["status"] = advance(rec.get("status", "CREATED"), nxt)
    rec.setdefault("lifecycle", []).append(rec["status"])


def _schema_status_for(n: dict) -> str:
    try:
        r = httpx.get(f"{n['url']}/metadata", timeout=2.0)
        if r.status_code != 200:
            return "UNKNOWN"
        data = r.json()
        if data.get("compatibility") == "INCOMPATIBLE" or data.get("canonical_model_version") != CANONICAL_EXPECTED:
            return "INCOMPATIBLE"
        return "COMPATIBLE"
    except Exception:
        return "UNKNOWN"


def _envelope(qid: str, spec: dict, rec: dict | None = None) -> dict:
    lab_code = spec.get("lab_test") or "HbA1c"
    if lab_code == "HbA1c":
        lab_code = "4548-4"
    eps = spec.get("epsilon") or DEFAULT_EPSILON
    k = strictest_k([n["id"] for n in _active_nodes()])
    return {
        "query_id": qid,
        "correlation_id": (rec or {}).get("correlation_id"),
        "trace_id": (rec or {}).get("trace_id"),
        "canonical_model_version": CANONICAL_EXPECTED,
        "schema_version": "1.0",
        "canonical_conditions": {
            "age_min": spec["age_min"],
            "age_max": spec["age_max"],
            "genders": spec.get("genders") or [],
            "condition": (spec.get("conditions") or [None])[0],
            "medication": (spec.get("medications") or [None])[0],
            "lab": {"code": lab_code, "operator": spec.get("lab_op") or ">", "value": spec.get("lab_value")},
            "window_months": spec.get("window_months") or 12,
            "year": spec.get("year"),
        },
        "privacy_policy": {
            "k": max(MIN_COHORT, k),
            "differential_privacy": bool(spec.get("differential_privacy")),
            "epsilon": eps if spec.get("differential_privacy") else None,
            "delta": spec.get("delta") or DEFAULT_DELTA,
        },
        "requested_fields": spec.get("requested_fields") or [],
        # legacy fields for older nodes
        "age_min": spec["age_min"],
        "age_max": spec["age_max"],
        "genders": spec.get("genders") or [],
        "conditions": spec.get("conditions") or [],
        "medications": spec.get("medications") or [],
        "lab_test": spec.get("lab_test"),
        "lab_op": spec.get("lab_op") or ">",
        "lab_value": spec.get("lab_value"),
        "window_months": spec.get("window_months") or 12,
        "year": spec.get("year"),
    }


def _call_node(n: dict, qid: str, spec: dict, rec: dict | None = None) -> NodeContribution:
    rec = rec or {}
    if rec.get("cancel_requested"):
        return NodeContribution(node_id=n["id"], node_name=n["name"], status="ERROR", error="cancelled")
    if rec.get("schema_status", {}).get(n["id"]) == "INCOMPATIBLE":
        return NodeContribution(node_id=n["id"], node_name=n["name"], status="ERROR", error="INCOMPATIBLE schema")
    payload = _envelope(qid, spec, rec)
    headers = svc_auth.issue(n["id"])
    last_err = "unknown"
    last_status = "ERROR"
    t0 = time.perf_counter()
    attempts = 0
    for attempt in range(NODE_RETRIES + 1):
        attempts = attempt + 1
        if rec.get("cancel_requested"):
            return NodeContribution(node_id=n["id"], node_name=n["name"], status="ERROR", error="cancelled")
        try:
            r = httpx.post(f"{n['url']}/query", json=payload, headers=headers, timeout=NODE_TIMEOUT)
            if r.status_code == 403:
                return NodeContribution(
                    node_id=n["id"],
                    node_name=n["name"],
                    status="ERROR",
                    error="node denied request",
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    attempts=attempts,
                )
            if r.status_code == 503:
                last_status, last_err = "OFFLINE", "unavailable"
            elif r.status_code != 200:
                last_status, last_err = "ERROR", f"HTTP {r.status_code}"
            else:
                data = r.json()
                # Isolation: reject unexpected patient-like keys
                for banned in ("patients", "rows", "records", "name", "phone"):
                    if banned in data:
                        return NodeContribution(
                            node_id=n["id"],
                            node_name=n["name"],
                            status="ERROR",
                            error="protocol violation: raw fields",
                            attempts=attempts,
                        )
                count = data.get("count")
                return NodeContribution(
                    node_id=n["id"],
                    node_name=n["name"],
                    status="OK",
                    count=None if count is None else int(count),
                    k_suppressed=bool(data.get("k_suppressed")),
                    dp_applied=bool(data.get("dp_applied")),
                    exact_eligible=data.get("exact_eligible"),
                    latency_ms=data.get("latency_ms"),
                    schema_version=data.get("schema_version"),
                    attempts=attempts,
                )
        except httpx.TimeoutException:
            last_status, last_err = "TIMEOUT", f"timeout after {NODE_TIMEOUT}s"
        except Exception:
            last_status, last_err = "OFFLINE", "connection failed"
        if attempt < NODE_RETRIES and last_status in {"TIMEOUT", "ERROR", "OFFLINE"}:
            time.sleep(0.15 * (2**attempt))
    return NodeContribution(
        node_id=n["id"],
        node_name=n["name"],
        status=last_status,
        error=last_err,
        latency_ms=(time.perf_counter() - t0) * 1000,
        attempts=attempts,
    )


@app.post("/queries/{qid}/execute")
def execute(qid: str, user: dict = Depends(require("query"))):
    rec = QUERIES.get(qid)
    if not rec:
        raise HTTPException(404, "query not found")
    if rec.get("cancel_requested") or rec.get("status") == "CANCELLED":
        raise HTTPException(409, "query cancelled")
    spec = rec["spec"]
    try:
        _set_state(rec, "VALIDATING")
        _set_state(rec, "PLANNING")
    except InvalidTransition as e:
        raise HTTPException(409, str(e))
    remaining = min(ledger.remaining(user["sub"], n["id"]) for n in _active_nodes()) if _active_nodes() else 0
    decision = evaluate_policy(
        role=user["role"],
        spec=spec,
        k_threshold=MIN_COHORT,
        budget_remaining=remaining,
        requested_epsilon=spec.get("epsilon") if spec.get("differential_privacy") else None,
        historical_count=_history_count(user["sub"]),
    )
    if not decision.allowed:
        rec["status"] = "DENIED"
        inc("fcqf_queries_denied")
        audit(user["sub"], user["role"], "POLICY_DENIED", qid, decision.reason)
        raise HTTPException(403, decision.reason)

    rec["schema_status"] = {n["id"]: _schema_status_for(n) for n in _active_nodes()}
    rec["plan"] = plan_query(spec, _active_nodes(), rec["schema_status"])
    use_dp = bool(spec.get("differential_privacy"))
    eps = None
    if use_dp:
        try:
            eps = validate_epsilon(spec.get("epsilon") or DEFAULT_EPSILON)
            validate_delta(spec.get("delta") or DEFAULT_DELTA)
        except DPError as e:
            raise HTTPException(400, str(e))
        try:
            for n in _active_nodes():
                ledger.consume(user["sub"], n["id"], eps)
                inc("fcqf_privacy_budget_consumed", eps)
        except DPError as e:
            raise HTTPException(403, str(e))

    t0 = time.perf_counter()
    try:
        _set_state(rec, "DISPATCHING")
        _set_state(rec, "RUNNING")
    except InvalidTransition:
        pass
    rec.setdefault("events", []).append("DISPATCHING")
    contribs: list[NodeContribution] = []
    targets = _active_nodes()
    with ThreadPoolExecutor(max_workers=max(1, len(targets))) as pool:
        futs = [pool.submit(_call_node, n, qid, spec, rec) for n in targets]
        for fut in as_completed(futs):
            if rec.get("cancel_requested"):
                break
            contribs.append(fut.result())
    if rec.get("cancel_requested"):
        rec["status"] = "CANCELLED"
        rec.setdefault("lifecycle", []).append("CANCELLED")
        audit(user["sub"], user["role"], "CANCELLED", qid, rec.get("trace_id", ""))
        raise HTTPException(409, "query cancelled")
    try:
        _set_state(rec, "AGGREGATING")
        _set_state(rec, "PRIVACY_CHECK")
    except InvalidTransition:
        pass
    contribs.sort(key=lambda c: c.node_id)

    ok = [c for c in contribs if c.status == "OK"]
    failed = [c for c in contribs if c.status != "OK"]
    released = [c.count for c in ok if c.count is not None and not c.k_suppressed]
    suppressed = [c for c in ok if c.k_suppressed or c.count is None]

    warnings: list[str] = []
    for c in suppressed:
        warnings.append(f"{c.node_name}: cohort < k={MIN_COHORT} suppressed")
    for c in failed:
        warnings.append(f"{c.node_name}: {c.status}")

    if not released and suppressed and not failed:
        status = ResultStatus.SUPPRESSED
        aggregate = None
        kind = "k_suppressed"
        complete = False
    elif failed and not ok:
        status = ResultStatus.FAILED
        aggregate = None
        kind = "none"
        complete = False
    elif failed:
        status = ResultStatus.PARTIAL
        aggregate = sum(released) if released else None
        kind = "differentially_private" if use_dp else "k_suppressed"
        complete = False
        warnings.append("Completeness is NOT GUARANTEED.")
    else:
        status = ResultStatus.COMPLETE
        aggregate = sum(released) if released else None
        kind = "differentially_private" if use_dp else ("exact" if not suppressed else "k_suppressed")
        complete = True
        if suppressed:
            kind = "differentially_private" if use_dp else "k_suppressed"

    if use_dp:
        kind = "differentially_private"

    executed_ms = round((time.perf_counter() - t0) * 1000, 2)
    nodes_total = len(contribs)
    nodes_ok = len(ok)
    completeness = round(100.0 * nodes_ok / nodes_total, 1) if nodes_total else 0.0

    privacy = {
        "min_cohort": MIN_COHORT,
        "suppressed_nodes": len(suppressed),
        "differential_privacy": use_dp,
        "epsilon": eps,
        "delta": (spec.get("delta") or DEFAULT_DELTA) if use_dp else None,
        "budget_remaining": ledger.snapshot(user["sub"]),
        "aggregate_kind": kind,
    }

    pid = str(uuid.uuid4())
    digest = hashlib.sha256(json.dumps(spec, sort_keys=True, default=str).encode()).hexdigest()[:16]
    result = QueryResult(
        query_id=qid,
        status=status,
        aggregate=aggregate,
        aggregate_kind=kind,
        completeness_guaranteed=complete,
        completeness=completeness,
        nodes_total=nodes_total,
        nodes_successful=nodes_ok,
        nodes_failed=len(failed),
        contributions=contribs,
        privacy=privacy,
        policy=decision.as_dict(),
        provenance_id=pid,
        warnings=warnings,
        executed_ms=executed_ms,
        created_at=datetime.now(timezone.utc),
    )
    dumped = result.model_dump(mode="json")
    rec["result"] = dumped
    rec["provenance_id"] = pid
    rec["executed_ms"] = executed_ms
    rec["status"] = {
        ResultStatus.COMPLETE: "COMPLETED",
        ResultStatus.PARTIAL: "PARTIAL",
        ResultStatus.SUPPRESSED: "SUPPRESSED",
        ResultStatus.FAILED: "FAILED",
    }.get(status, "FAILED")
    rec.setdefault("lifecycle", []).append(rec["status"])
    rec["explain"] = explain_plan([c.model_dump() for c in contribs], rec.get("schema_status") or {}, True, use_dp)
    rec.setdefault("events", []).extend(["AGGREGATION_COMPLETED", "RESULT_RETURNED"])
    observe("fcqf_query_latency", executed_ms)
    if status == ResultStatus.COMPLETE:
        inc("fcqf_queries_completed")
    elif status == ResultStatus.PARTIAL:
        inc("fcqf_queries_partial")
    if suppressed:
        inc("fcqf_suppressed_results", len(suppressed))
    for c in failed:
        inc("fcqf_node_failures")

    payload = {
        "query_id": qid,
        "canonical_query": spec,
        "actor": user["sub"],
        "role": user["role"],
        "purpose": user.get("purpose"),
        "participating_nodes": [c.node_id for c in contribs],
        "successful_nodes": [c.node_id for c in ok],
        "failed_nodes": [c.node_id for c in failed],
        "schema_versions": {c.node_id: c.schema_version for c in contribs},
        "policy": decision.as_dict(),
        "k_anonymity": {"k": MIN_COHORT, "suppressed": len(suppressed)},
        "differential_privacy": {"enabled": use_dp, "epsilon": eps, "delta": privacy["delta"]},
        "privacy_budget_consumed": eps if use_dp else 0,
        "privacy_budget_remaining": privacy["budget_remaining"],
        "status": status.value,
        "result_digest": hashlib.sha256(json.dumps(dumped, sort_keys=True, default=str).encode()).hexdigest()[:16],
        "digest": digest,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }
    con = sqlite3.connect(AUDIT_DB)
    con.execute(
        "INSERT INTO provenance (id,query_id,payload,created_at) VALUES (?,?,?,?)",
        (pid, qid, json.dumps(payload), payload["executed_at"]),
    )
    con.commit()
    con.close()
    audit(user["sub"], user["role"], "execute", qid, status.value)
    return dumped


@app.get("/queries/{qid}/result")
def get_result(qid: str, user: dict = Depends(require("read_result"))):
    rec = QUERIES.get(qid)
    if not rec or not rec.get("result"):
        raise HTTPException(404, "result not available")
    return rec["result"]


@app.get("/queries/{qid}/provenance")
def get_prov(qid: str, user: dict = Depends(require("read_provenance"))):
    rec = QUERIES.get(qid)
    if not rec or not rec.get("provenance_id"):
        raise HTTPException(404, "provenance not available")
    con = sqlite3.connect(AUDIT_DB)
    row = con.execute("SELECT payload FROM provenance WHERE id=?", (rec["provenance_id"],)).fetchone()
    con.close()
    if not row:
        raise HTTPException(404, "provenance missing")
    return json.loads(row[0])


@app.get("/audit/logs")
def audit_logs(user: dict = Depends(require("read_audit"))):
    con = sqlite3.connect(AUDIT_DB)
    rows = con.execute(
        "SELECT id,ts,actor,role,action,query_id,detail FROM audit ORDER BY id DESC LIMIT 200"
    ).fetchall()
    con.close()
    return [
        {
            "id": r[0],
            "ts": r[1],
            "actor": r[2],
            "role": r[3],
            "action": r[4],
            "query_id": r[5],
            "detail": r[6][:400],
        }
        for r in rows
    ]


@app.get("/privacy/budget")
def budget(user: dict = Depends(current_user)):
    return {"actor": user["sub"], "remaining": ledger.snapshot(user["sub"]), "default": BUDGET}


@app.get("/", response_class=HTMLResponse)
def gateway_home():
    cards = []
    for n in NODES:
        p = _probe(n)
        color = "#16A34A" if p.get("healthy") else "#DC2626"
        cards.append(
            f"""<div class="card"><div class="row"><span class="dot" style="background:{color}"></span>
            <strong>{p.get('name')}</strong></div>
            <div class="meta">{p.get('status')} · {p.get('latency_ms')} ms · schema {p.get('schema_version') or 'n/a'}
            · local patients {p.get('patient_count') if p.get('patient_count') is not None else 'n/a'}</div></div>"""
        )
    html = f"""<!doctype html><html><head><meta charset="utf-8"/><title>FCQF API Gateway</title>
    <style>
      body{{font-family:Inter,system-ui,sans-serif;background:#F6F8FB;color:#172033;margin:0;padding:32px}}
      h1{{margin:0 0 6px}} .sub{{color:#667085;margin-bottom:24px}}
      .card{{background:#fff;border:1px solid #E4E7EC;border-radius:14px;padding:16px;margin:10px 0;box-shadow:0 1px 2px rgba(16,24,40,.04)}}
      .row{{display:flex;align-items:center;gap:8px}} .dot{{width:10px;height:10px;border-radius:50%;display:inline-block}}
      .meta{{color:#667085;font-size:13px;margin-top:6px}} a{{color:#2563EB}}
      code{{background:#EFF6FF;padding:2px 6px;border-radius:6px}}
    </style></head><body>
    <h1>FCQF API Gateway</h1>
    <p class="sub">Coordinator · port 8080 · live federation status (no patient records)</p>
    {''.join(cards)}
    <div class="card"><div>OpenAPI <a href="/docs">/docs</a> · Health <a href="/health">/health</a> · Metrics <a href="/metrics">/metrics</a></div>
    <div class="meta">Dashboard UI is on port <code>5173</code>. Login: researcher / research123</div></div>
    </body></html>"""
    return HTMLResponse(html)


@app.get("/health")
def gw_health():
    return {"ok": True, "service": "gateway", "version": "0.13.0"}


@app.get("/metrics")
def metrics():
    return PlainTextResponse(render_metrics(), media_type="text/plain")


@app.post("/queries/{qid}/cancel")
def cancel_query(qid: str, user: dict = Depends(require("query"))):
    rec = QUERIES.get(qid)
    if not rec:
        raise HTTPException(404, "query not found")
    rec["cancel_requested"] = True
    if rec.get("status") not in {"COMPLETED", "PARTIAL", "SUPPRESSED", "FAILED", "DENIED", "TIMEOUT"}:
        rec["status"] = "CANCELLED"
        rec.setdefault("lifecycle", []).append("CANCELLED")
    audit(user["sub"], user["role"], "CANCELLED", qid, rec.get("trace_id", ""))
    return {"query_id": qid, "status": rec["status"]}


@app.post("/queries/{qid}/execute-async")
def execute_async(qid: str, user: dict = Depends(require("query"))):
    rec = QUERIES.get(qid)
    if not rec:
        raise HTTPException(404, "query not found")
    rec["status"] = rec.get("status") or "CREATED"

    def _run():
        try:
            execute(qid, user)
        except HTTPException:
            pass

    ThreadPoolExecutor(max_workers=1).submit(_run)
    return {"query_id": qid, "status": "RUNNING"}


@app.get("/queries/{qid}/explain")
def query_explain(qid: str, user: dict = Depends(require("query", "read_result"))):
    rec = QUERIES.get(qid)
    if not rec:
        raise HTTPException(404, "query not found")
    return {"query_id": qid, "plan": rec.get("plan"), "explain": rec.get("explain"), "lifecycle": rec.get("lifecycle")}


@app.get("/topology")
def topology(user: dict = Depends(require("read_nodes", "query"))):
    nodes = [_probe(n) for n in NODES]
    for n, p in zip(NODES, nodes):
        p["policy"] = PROFILES.get(n["id"], {}).get("privacy")
        p["active"] = n.get("active", True)
        p["schema_compatibility"] = _schema_status_for(n) if p.get("healthy") else "UNKNOWN"
    return {"coordinator": "FCQF", "nodes": nodes}


class InstitutionIn(BaseModel):
    id: str
    name: str
    url: str


@app.get("/institutions")
def list_institutions(user: dict = Depends(require("read_nodes", "admin"))):
    return [{"id": n["id"], "name": n["name"], "url": n["url"], "active": n.get("active", True)} for n in NODES]


@app.post("/institutions")
def register_institution(body: InstitutionIn, user: dict = Depends(require("admin"))):
    if any(n["id"] == body.id for n in NODES):
        raise HTTPException(409, "already registered")
    NODES.append({"id": body.id, "name": body.name, "url": body.url, "active": False})
    audit(user["sub"], user["role"], "INSTITUTION_REGISTERED", None, body.id)
    return {"id": body.id, "status": "REGISTERED"}


@app.post("/institutions/{iid}/activate")
def activate_institution(iid: str, user: dict = Depends(require("admin"))):
    n = next((x for x in NODES if x["id"] == iid), None)
    if not n:
        raise HTTPException(404, "unknown institution")
    probe = _probe(n)
    compat = _schema_status_for(n) if probe.get("healthy") else "UNKNOWN"
    if not probe.get("healthy") or compat == "INCOMPATIBLE":
        return {"id": iid, "status": "ONBOARDING_FAILED", "health": probe, "schema": compat}
    n["active"] = True
    audit(user["sub"], user["role"], "INSTITUTION_ACTIVE", None, iid)
    return {"id": iid, "status": "ACTIVE", "schema": compat}


@app.post("/auth/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("fcqf_access", path="/")
    return resp


@app.get("/auth/me")
def auth_me(user: dict = Depends(current_user)):
    return {
        "username": user.get("sub"),
        "role": user.get("role"),
        "purpose": user.get("purpose"),
        "permissions": sorted(ROLE_PERMS.get(user.get("role", ""), set())),
    }


@app.get("/config")
def public_config():
    return {
        "environment": FCQF_ENV,
        "demo_accounts": False,
        "min_cohort": MIN_COHORT,
        "version": "0.13.0",
    }


@app.post("/queries/preview-policy")
def preview_policy(q: QueryCreate, user: dict = Depends(require("query", "read_result"))):
    spec = q.model_dump()
    remaining = min((ledger.remaining(user["sub"], n["id"]) for n in _active_nodes()), default=BUDGET)
    decision = evaluate_policy(
        role=user["role"],
        spec=spec,
        k_threshold=MIN_COHORT,
        budget_remaining=remaining,
        requested_epsilon=spec.get("epsilon") if spec.get("differential_privacy") else None,
        historical_count=_history_count(user["sub"]),
    )
    return decision.as_dict()


@app.get("/stats")
def dashboard_stats(user: dict = Depends(require("read_result", "query", "read_nodes"))):
    nodes = [_probe(n) for n in NODES]
    today = datetime.now(timezone.utc).date().isoformat()
    recs = list(QUERIES.values())
    today_q = [r for r in recs if str(r.get("created_at", "")).startswith(today)]
    statuses = [r.get("status") for r in recs]
    latencies = [r.get("executed_ms") for r in recs if r.get("executed_ms") is not None]
    suppressed = sum(1 for r in recs if r.get("status") == "SUPPRESSED")
    snap = ledger.snapshot(user["sub"])
    used = 0.0
    if snap:
        used = max(0.0, BUDGET * len(snap) - sum(snap.values()))
    denom = BUDGET * max(1, len(NODES))
    return {
        "active_institutions": len(NODES),
        "online_nodes": sum(1 for n in nodes if n.get("healthy")),
        "nodes_total": len(nodes),
        "queries_today": len(today_q),
        "queries_total": len(recs),
        "complete_queries": statuses.count("COMPLETED") + statuses.count("COMPLETE"),
        "partial_queries": statuses.count("PARTIAL"),
        "suppressed_results": suppressed,
        "privacy_budget_used_pct": round(100.0 * used / denom, 1) if denom else 0,
        "average_query_ms": round(sum(latencies) / len(latencies), 1) if latencies else None,
        "environment": FCQF_ENV,
        "nodes": nodes,
    }


@app.get("/benchmarks")
def get_benchmarks(user: dict = Depends(require("read_result", "query", "read_nodes"))):
    path = ROOT / "benchmark" / "results.json"
    if not path.exists():
        return {"available": False, "results": None}
    return {"available": True, "results": json.loads(path.read_text())}


@app.get("/audit/logs/{eid}")
def audit_detail(eid: int, user: dict = Depends(require("read_audit"))):
    con = sqlite3.connect(AUDIT_DB)
    r = con.execute(
        "SELECT id,ts,actor,role,action,query_id,detail FROM audit WHERE id=?", (eid,)
    ).fetchone()
    con.close()
    if not r:
        raise HTTPException(404, "event not found")
    return {
        "id": r[0],
        "ts": r[1],
        "actor": r[2],
        "role": r[3],
        "action": r[4],
        "query_id": r[5],
        "detail": r[6],
    }


@app.get("/institutions/{iid}")
def institution_detail(iid: str, user: dict = Depends(require("read_nodes", "query"))):
    n = next((x for x in NODES if x["id"] == iid), None)
    catalog_row = None
    try:
        con = _catalog()
        catalog_row = con.execute(
            "SELECT institution_id, institution_name, institution_type, location, node_id FROM institutions WHERE institution_id=? OR node_id=?",
            (iid, iid),
        ).fetchone()
        con.close()
    except HTTPException:
        catalog_row = None
    if not n and catalog_row and catalog_row["node_id"]:
        n = next((x for x in NODES if x["id"] == catalog_row["node_id"]), None)
    if not n and not catalog_row:
        raise HTTPException(404, "unknown institution")
    probe = _probe(n) if n else {"healthy": False, "status": "UNASSIGNED", "name": iid}
    nid = (n or {}).get("id", iid)
    prof = PROFILES.get(nid, {})
    name = (catalog_row["institution_name"] if catalog_row else None) or probe.get("name") or iid
    itype = (catalog_row["institution_type"] if catalog_row else None) or (
        "laboratory" if "lab" in iid else "hospital" if "hospital" in iid else "research"
    )
    return {
        **probe,
        "id": iid,
        "name": name,
        "type": itype,
        "location": catalog_row["location"] if catalog_row else None,
        "institution_id": catalog_row["institution_id"] if catalog_row else iid,
        "node_id": (catalog_row["node_id"] if catalog_row else None) or nid,
        "profile": prof,
        "schema_compatibility": _schema_status_for(n) if n else "UNKNOWN",
        "canonical_model_version": prof.get("canonical_model_version"),
        "agent_version": "1.0",
        "allowed_query_types": prof.get("allowed_query_types", []),
        "privacy": prof.get("privacy", {}),
    }


@app.get("/docs/catalog")
def docs_catalog(user: dict = Depends(current_user)):
    docs_dir = ROOT / "docs"
    items = []
    if docs_dir.exists():
        for p in sorted(docs_dir.glob("*.md")):
            items.append({"id": p.stem, "title": p.stem.replace("_", " ").title(), "path": f"docs/{p.name}"})
    return items


@app.get("/docs/catalog/{doc_id}")
def docs_content(doc_id: str, user: dict = Depends(current_user)):
    p = (ROOT / "docs" / f"{doc_id}.md").resolve()
    if ROOT / "docs" not in p.parents or not p.exists():
        raise HTTPException(404, "document not found")
    return {"id": doc_id, "title": doc_id.replace("_", " ").title(), "markdown": p.read_text()[:20000]}


def _catalog() -> sqlite3.Connection:
    path = STORE / "catalog.db"
    if not path.exists():
        raise HTTPException(503, "epidemiology catalog not loaded")
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


@app.get("/catalog/diseases")
def catalog_diseases(user: dict = Depends(require("query", "read_result", "read_nodes"))):
    con = _catalog()
    rows = con.execute("SELECT disease_id, disease_name, disease_category, icd10_code FROM diseases ORDER BY disease_name").fetchall()
    con.close()
    return [dict(r) for r in rows]


@app.get("/catalog/institutions")
def catalog_institutions(user: dict = Depends(require("read_nodes", "query", "read_result"))):
    con = _catalog()
    rows = con.execute(
        "SELECT institution_id, institution_name, institution_type, location, node_id FROM institutions ORDER BY institution_id"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


@app.get("/catalog/years")
def catalog_years(user: dict = Depends(require("query", "read_result", "read_nodes"))):
    return {"years": list(range(2015, 2027))}


def _node_get(n: dict, path: str) -> dict | None:
    try:
        r = httpx.get(f"{n['url']}{path}", headers=svc_auth.issue(n["id"]), timeout=4.0)
        if r.status_code != 200:
            return None
        data = r.json()
        if isinstance(data, dict) and any(k in data for k in ("patients", "rows", "records")):
            return None
        return data if isinstance(data, dict) else None
    except Exception:
        return None


@app.get("/analytics/overview")
def analytics_overview(
    disease: str = "Type 2 diabetes mellitus",
    user: dict = Depends(require("query", "read_result", "read_nodes")),
):
    from urllib.parse import quote

    nodes = []
    series_by_year: dict[int, dict[str, Any]] = {}
    top_merge: dict[str, dict[str, Any]] = {}
    for n in _active_nodes():
        summary = _node_get(n, "/epi/summary") or {}
        trend = _node_get(n, "/epi/trend?disease=" + quote(disease)) or {}
        healthy = bool(summary.get("node_id") or trend.get("node_id"))
        nodes.append(
            {
                "node_id": n["id"],
                "name": n["name"],
                "healthy": healthy,
                "k": summary.get("k"),
                "year_min": summary.get("year_min"),
                "year_max": summary.get("year_max"),
                "top_diseases": summary.get("top_diseases") or [],
                "trend": trend.get("series") or [],
            }
        )
        for item in summary.get("top_diseases") or []:
            key = str(item.get("disease_name") or item.get("disease_id"))
            rec = top_merge.setdefault(
                key,
                {
                    "disease_name": item.get("disease_name"),
                    "icd10_code": item.get("icd10_code"),
                    "category": item.get("category"),
                    "count": 0,
                    "nodes": 0,
                },
            )
            rec["count"] += int(item.get("count") or 0)
            rec["nodes"] += 1
        for pt in trend.get("series") or []:
            y = int(pt.get("year"))
            bucket = series_by_year.setdefault(y, {"year": y, "total": 0})
            val = pt.get("count")
            bucket[n["id"]] = val
            if isinstance(val, int):
                bucket["total"] = int(bucket.get("total") or 0) + val
    top = sorted(top_merge.values(), key=lambda x: int(x["count"]), reverse=True)[:10]
    timeline = [series_by_year[y] for y in sorted(series_by_year)]
    return {
        "disease": disease,
        "nodes": nodes,
        "timeline": timeline,
        "top_diseases": top,
        "completeness_note": "Yearly counts are node-local aggregates with k-suppression. No patient rows.",
    }


@app.get("/analytics/node/{node_id}")
def analytics_node(node_id: str, user: dict = Depends(require("query", "read_result", "read_nodes"))):
    n = next((x for x in NODES if x["id"] == node_id), None)
    if not n:
        raise HTTPException(404, "unknown node")
    summary = _node_get(n, "/epi/summary")
    if not summary:
        raise HTTPException(503, "node analytics unavailable")
    return summary
