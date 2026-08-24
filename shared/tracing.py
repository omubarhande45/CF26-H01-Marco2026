"""Correlation / query / trace identifiers. Never include PHI."""
from __future__ import annotations

import uuid


def new_ids(query_id: str | None = None) -> dict[str, str]:
    qid = query_id or str(uuid.uuid4())
    return {
        "query_id": qid,
        "correlation_id": str(uuid.uuid4()),
        "trace_id": uuid.uuid4().hex[:16],
    }


SENSITIVE = ("patient_id", "pat_id", "name", "phone", "address", "ssn", "mrn", "dob")


def safe_log(msg: str) -> str:
    low = msg.lower()
    for s in SENSITIVE:
        if s in low:
            return "[redacted]"
    return msg
