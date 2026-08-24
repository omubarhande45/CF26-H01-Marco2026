"""Institutional data node: local aggregate API only — never returns raw patients."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gateway.service_auth import build_service_auth
from institutions.profiles import PROFILES
from privacy.dp import LaplaceMechanism
from privacy.policy import FORBIDDEN_FIELDS
from schema_mapper.epi import names_match
from schema_mapper.mappings import GENDER_LOCAL, LOCAL_DX, LOCAL_LAB, LOCAL_MED, NODE_SQL
from shared.tracing import safe_log

NODE_ID = os.environ.get("NODE_ID", "hospital_a")
NODE_NAME = os.environ.get("NODE_NAME", "Hospital A")
DB_PATH = os.environ.get("DB_PATH", str(ROOT / "institutional_nodes" / "data" / f"{NODE_ID}.db"))
_prof = PROFILES.get(NODE_ID, {})
SCHEMA_VERSION = os.environ.get("SCHEMA_VERSION", str(_prof.get("schema_version", "1.0.0")))
CANONICAL_MODEL = os.environ.get("CANONICAL_MODEL_VERSION", str(_prof.get("canonical_model_version", "1.0")))
AGENT_VERSION = "1.0"
OFFLINE = os.environ.get("FORCE_OFFLINE", "0") == "1"
FORCE_SLOW = float(os.environ.get("FORCE_SLOW", "0") or 0)
FORCE_INCOMPATIBLE = os.environ.get("FORCE_INCOMPATIBLE", "0") == "1"
FORCE_MALFORMED = os.environ.get("FORCE_MALFORMED", "0") == "1"
NODE_K = int(os.environ.get("NODE_K", _prof.get("privacy", {}).get("minimum_cohort", 10)))
svc_auth = build_service_auth()
AUDIT_PATH = Path(os.environ.get("NODE_AUDIT", str(ROOT / "institutional_nodes" / "data" / f"{NODE_ID}_audit.db")))

app = FastAPI(title=f"FCQF Node {NODE_NAME}", version=SCHEMA_VERSION)
_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_dp = LaplaceMechanism()


class LocalQuery(BaseModel):
    """Backward-compatible local query plus secure-protocol fields."""

    query_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    schema_version: str = "1.0"
    canonical_model_version: str = "1.0"
    age_min: int = 0
    age_max: int = 120
    genders: list[str] = []
    conditions: list[str] = []
    medications: list[str] = []
    lab_test: str | None = None
    lab_op: str = ">"
    lab_value: float | None = None
    window_months: int = 12
    year: int | None = None
    requested_fields: list[str] = Field(default_factory=list)
    return_rows: bool = False
    canonical_conditions: dict | None = None
    privacy_policy: dict | None = None


def _init_audit():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(AUDIT_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS node_audit (id INTEGER PRIMARY KEY, ts TEXT, query_id TEXT, action TEXT, detail TEXT)"
    )
    con.commit()
    con.close()


_init_audit()


def _node_audit(qid: str | None, action: str, detail: str):
    con = sqlite3.connect(AUDIT_PATH)
    con.execute(
        "INSERT INTO node_audit (ts,query_id,action,detail) VALUES (?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), qid, action, detail[:500]),
    )
    con.commit()
    con.close()


def _sql_list(values: list[str]) -> str:
    # Only emit quoted literals after escaping; values must already be mapped allow-list terms.
    if not values:
        return "''"
    out = []
    for v in values:
        if not isinstance(v, str) or any(c in v for c in ";\\"):
            continue
        out.append("'" + v.replace("'", "''") + "'")
    return ",".join(out) if out else "''"


def _conn() -> sqlite3.Connection:
    if not Path(DB_PATH).exists():
        raise HTTPException(503, "database unavailable")
    con = sqlite3.connect(DB_PATH, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def _expand_from_protocol(q: LocalQuery) -> LocalQuery:
    cc = q.canonical_conditions or {}
    if cc:
        if cc.get("condition") and not q.conditions:
            cond = cc["condition"]
            q.conditions = [cond] if isinstance(cond, str) else list(cond)
        if cc.get("medication") and not q.medications:
            med = cc["medication"]
            q.medications = [med] if isinstance(med, str) else list(med)
        lab = cc.get("lab") or {}
        if lab:
            q.lab_test = q.lab_test or lab.get("code") or lab.get("test")
            q.lab_op = lab.get("operator") or q.lab_op
            if q.lab_value is None:
                q.lab_value = lab.get("value")
        if "age_min" in cc:
            q.age_min = int(cc["age_min"])
        if "age_max" in cc:
            q.age_max = int(cc["age_max"])
        if "window_months" in cc:
            q.window_months = int(cc["window_months"])
        if "genders" in cc:
            q.genders = list(cc["genders"])
    if cc.get("year") is not None:
            q.year = int(cc["year"])
    return q


def _query_epidemiology(q: LocalQuery) -> int | None:
    """Aggregate counts from loaded institutional epidemiology tables. No patient rows."""
    if not Path(DB_PATH).exists():
        return None
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        con.execute("SELECT 1 FROM epi_diseases LIMIT 1")
    except sqlite3.Error:
        con.close()
        return None
    conds = [c for c in (q.conditions or []) if c]
    year = q.year
    if not conds:
        sql = "SELECT COALESCE(SUM(disease_count),0) FROM epi_records"
        params: list = []
        if year:
            sql += " WHERE year=?"
            params.append(year)
        n = int(con.execute(sql, params).fetchone()[0])
        con.close()
        return n
    if len(conds) == 1:
        diseases = con.execute("SELECT disease_id, disease_name, icd10_code FROM epi_diseases").fetchall()
        ids = [
            d["disease_id"]
            for d in diseases
            if names_match(conds[0], d["disease_name"]) or names_match(conds[0], d["icd10_code"] or "")
        ]
        if not ids:
            con.close()
            return 0
        ph = ",".join("?" * len(ids))
        sql = f"SELECT COALESCE(SUM(disease_count),0) FROM epi_records WHERE disease_id IN ({ph})"
        params = list(ids)
        if year:
            sql += " AND year=?"
            params.append(year)
        n = int(con.execute(sql, params).fetchone()[0])
        con.close()
        return n
    rows = con.execute(
        "SELECT disease_1, disease_2, disease_3, disease_4, patient_count, year FROM epi_combinations"
    ).fetchall()
    total = 0
    want = list(conds)
    for r in rows:
        if year and int(r["year"]) != int(year):
            continue
        parts = [p for p in (r["disease_1"], r["disease_2"], r["disease_3"], r["disease_4"]) if p]
        if len(parts) != len(want):
            continue
        used = [False] * len(parts)
        ok = True
        for w in want:
            hit = False
            for i, part in enumerate(parts):
                if not used[i] and names_match(w, part):
                    used[i] = True
                    hit = True
                    break
            if not hit:
                ok = False
                break
        if ok:
            total += int(r["patient_count"] or 0)
    con.close()
    return total


@app.get("/", response_class=HTMLResponse)
def node_home():
    try:
        h = health()
        status = h.get("status", "AVAILABLE")
        count = h.get("patient_count")
        schema = h.get("schema_version")
        k = h.get("k_threshold")
        color = "#16A34A"
    except Exception:
        status, count, schema, k, color = "OFFLINE", "n/a", "n/a", "n/a", "#DC2626"
    return HTMLResponse(
        f"""<!doctype html><html><head><meta charset="utf-8"/><title>{NODE_NAME}</title>
<style>body{{font-family:Inter,system-ui,sans-serif;background:#F6F8FB;color:#172033;margin:0;padding:32px}}
.card{{background:#fff;border:1px solid #E4E7EC;border-radius:14px;padding:20px;max-width:560px}}
.dot{{width:10px;height:10px;border-radius:50%;display:inline-block;background:{color};margin-right:8px}}
.meta{{color:#667085;font-size:14px;line-height:1.7}} a{{color:#2563EB}}</style></head><body>
<div class="card"><h1><span class="dot"></span>{NODE_NAME}</h1>
<p>Institutional federation agent · <strong>{NODE_ID}</strong></p>
<div class="meta">Status: {status}<br/>Schema: {schema} · Canonical 1.0 · Agent {AGENT_VERSION}<br/>
Local synthetic patients: {count}<br/>k-threshold: {k}<br/>
This node never returns raw patient records. Only aggregates via POST /query.</div>
<p class="meta"><a href="/health">/health</a> · <a href="/metadata">/metadata</a> · <a href="/docs">/docs</a></p>
</div></body></html>"""
    )


@app.get("/health")
def health():
    if OFFLINE:
        raise HTTPException(503, "node forced offline")
    t0 = time.perf_counter()
    con = _conn()
    n = None
    for table in ("patients", "person", "fhir_patient", "subject"):
        try:
            n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            break
        except sqlite3.Error:
            continue
    con.close()
    return {
        "node_id": NODE_ID,
        "name": NODE_NAME,
        "healthy": True,
        "status": "AVAILABLE",
        "institution": NODE_ID,
        "schema_version": "99.0" if FORCE_INCOMPATIBLE else SCHEMA_VERSION,
        "canonical_model_version": CANONICAL_MODEL,
        "agent_version": AGENT_VERSION,
        "patient_count": n,
        "k_threshold": NODE_K,
        "privacy_policy": _prof.get("privacy", {}),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
    }


@app.get("/metadata")
def metadata():
    return {
        "institution": NODE_ID,
        "schema_version": "99.0" if FORCE_INCOMPATIBLE else SCHEMA_VERSION,
        "canonical_model_version": CANONICAL_MODEL,
        "agent_version": AGENT_VERSION,
        "compatibility": "INCOMPATIBLE" if FORCE_INCOMPATIBLE else "COMPATIBLE",
    }


@app.post("/query")
def query(q: LocalQuery, request: Request):
    if OFFLINE:
        raise HTTPException(503, "node forced offline")
    q = _expand_from_protocol(q)
    fields = {f.lower() for f in (q.requested_fields or [])}
    if fields & FORBIDDEN_FIELDS or q.return_rows:
        _node_audit(q.query_id, "denied_raw", json.dumps(sorted(fields)))
        raise HTTPException(403, "Raw patient-level data is prohibited.")

    t0 = time.perf_counter()
    epi = _query_epidemiology(q)
    if epi is not None:
        pol = q.privacy_policy or {}
        k = int(pol.get("k", NODE_K))
        k_suppressed = epi < k
        released = None if k_suppressed else epi
        dp_applied = False
        if released is not None and pol.get("differential_privacy"):
            released = _dp.protect_count(released, float(pol.get("epsilon") or 1.0))
            dp_applied = True
        _node_audit(q.query_id, "epi_query", f"count={released} k_suppressed={k_suppressed}")
        return {
            "node_id": NODE_ID,
            "node_name": NODE_NAME,
            "status": "OK",
            "count": released,
            "k_suppressed": k_suppressed,
            "dp_applied": dp_applied,
            "exact_eligible": not k_suppressed and not dp_applied,
            "schema_version": SCHEMA_VERSION,
            "source": "epidemiology",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }

    if NODE_ID not in NODE_SQL:
        raise HTTPException(500, "unknown node configuration")
    template = NODE_SQL[NODE_ID]["count_cohort"]

    dx_locals: list[str] = []
    for c in q.conditions:
        mapped = LOCAL_DX[NODE_ID].get(c)
        if mapped:
            dx_locals.extend(mapped)
        # unmapped free text is ignored (no injection of arbitrary codes)
    med_locals: list[str] = []
    for m in q.medications:
        mapped = LOCAL_MED[NODE_ID].get(m)
        if mapped:
            med_locals.extend(mapped)
    lab_key = q.lab_test or "HbA1c"
    # accept LOINC or canonical
    if lab_key in ("4548-4", "A1C", "Hemoglobin A1c"):
        lab_key = "HbA1c"
    lab_locals = LOCAL_LAB[NODE_ID].get(lab_key, [])
    genders = [GENDER_LOCAL[NODE_ID][g.lower()] for g in q.genders if g.lower() in GENDER_LOCAL[NODE_ID]]

    op = q.lab_op if q.lab_op in (">", ">=", "<", "<=", "=") else ">"
    sql = template.format(
        genders=_sql_list(genders or ["__none__"]),
        dx_codes=_sql_list(dx_locals or ["__none__"]),
        drugs=_sql_list(med_locals or ["__none__"]),
        labs=_sql_list(lab_locals or ["__none__"]),
        lab_op=op,
    )
    params = {
        "age_min": q.age_min,
        "age_max": q.age_max,
        "gender_filter": 1 if genders else 0,
        "need_dx": 1 if dx_locals else 0,
        "need_med": 1 if med_locals else 0,
        "need_lab": 1 if q.lab_value is not None else 0,
        "lab_value": q.lab_value if q.lab_value is not None else 0,
        "window": f"-{int(q.window_months)} months",
    }
    con = _conn()
    try:
        row = con.execute(sql, params).fetchone()
        exact = int(row[0]) if row else 0
    except sqlite3.Error:
        con.close()
        _node_audit(q.query_id, "error", "local query failed")
        raise HTTPException(400, "local query failed")
    con.close()

    pol = q.privacy_policy or {}
    k = int(pol.get("k", NODE_K))
    k_suppressed = exact < k
    released = None if k_suppressed else exact
    dp_applied = False
    if released is not None and pol.get("differential_privacy"):
        eps = float(pol.get("epsilon") or 1.0)
        released = _dp.protect_count(released, eps)
        dp_applied = True

    _node_audit(q.query_id, "query", f"k_suppressed={k_suppressed} dp={dp_applied} trace={q.trace_id}")
    if FORCE_MALFORMED:
        return {"name": "leak", "patients": [{"id": 1}]}
    return {
        "node_id": NODE_ID,
        "node_name": NODE_NAME,
        "status": "OK",
        "count": released,
        "k_suppressed": k_suppressed,
        "dp_applied": dp_applied,
        "exact_eligible": not k_suppressed and not dp_applied,
        "schema_version": SCHEMA_VERSION,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
    }


def _disease_ids_for(con: sqlite3.Connection, name: str) -> list[str]:
    diseases = con.execute("SELECT disease_id, disease_name, icd10_code FROM epi_diseases").fetchall()
    return [
        d["disease_id"]
        for d in diseases
        if names_match(name, d["disease_name"]) or names_match(name, d["icd10_code"] or "")
    ]


@app.get("/epi/summary")
def epi_summary():
    """Local disease aggregates only. Counts below k are omitted."""
    if OFFLINE:
        raise HTTPException(503, "node forced offline")
    if not Path(DB_PATH).exists():
        raise HTTPException(503, "database unavailable")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        con.execute("SELECT 1 FROM epi_records LIMIT 1")
    except sqlite3.Error:
        con.close()
        raise HTTPException(503, "epidemiology not loaded")
    years = con.execute("SELECT MIN(year), MAX(year), COUNT(*) FROM epi_records").fetchone()
    rows = con.execute(
        """
        SELECT d.disease_id, d.disease_name, d.icd10_code, d.disease_category, SUM(r.disease_count) AS c
        FROM epi_records r JOIN epi_diseases d ON d.disease_id = r.disease_id
        GROUP BY d.disease_id
        ORDER BY c DESC
        LIMIT 12
        """
    ).fetchall()
    con.close()
    top = []
    for r in rows:
        c = int(r["c"] or 0)
        if c < NODE_K:
            continue
        top.append(
            {
                "disease_id": r["disease_id"],
                "disease_name": r["disease_name"],
                "icd10_code": r["icd10_code"],
                "category": r["disease_category"],
                "count": c,
            }
        )
    return {
        "node_id": NODE_ID,
        "node_name": NODE_NAME,
        "k": NODE_K,
        "year_min": years[0],
        "year_max": years[1],
        "record_rows": years[2],
        "top_diseases": top,
    }


@app.get("/epi/trend")
def epi_trend(disease: str = "Type 2 diabetes mellitus"):
    if OFFLINE:
        raise HTTPException(503, "node forced offline")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        ids = _disease_ids_for(con, disease)
        if not ids:
            con.close()
            return {"node_id": NODE_ID, "node_name": NODE_NAME, "disease": disease, "series": []}
        ph = ",".join("?" * len(ids))
        rows = con.execute(
            f"SELECT year, SUM(disease_count) AS c FROM epi_records WHERE disease_id IN ({ph}) GROUP BY year ORDER BY year",
            ids,
        ).fetchall()
    except sqlite3.Error:
        con.close()
        raise HTTPException(503, "epidemiology not loaded")
    con.close()
    series = []
    for r in rows:
        c = int(r["c"] or 0)
        series.append({"year": int(r["year"]), "count": None if c < NODE_K else c, "suppressed": c < NODE_K})
    return {"node_id": NODE_ID, "node_name": NODE_NAME, "disease": disease, "series": series}


@app.post("/validate")
def validate():
    h = health()
    return {"valid": h["healthy"], "schema_version": SCHEMA_VERSION, "node_id": NODE_ID}


@app.get("/audit")
def local_audit():
    con = sqlite3.connect(AUDIT_PATH)
    rows = con.execute("SELECT ts,query_id,action FROM node_audit ORDER BY id DESC LIMIT 50").fetchall()
    con.close()
    return [{"ts": r[0], "query_id": r[1], "action": r[2]} for r in rows]
