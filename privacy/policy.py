"""Pre-execution privacy policy. Never silently allow a violating query."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

FORBIDDEN_FIELDS = {
    "patient_id",
    "pat_id",
    "patient_key",
    "resource_id",
    "name",
    "full_name",
    "phone",
    "address",
    "ssn",
    "email",
    "dob",
    "mrn",
    "identifier",
}

ALLOWED_AGG = {"count_distinct_patients", "count"}
ALLOWED_LAB_OPS = {">", ">=", "<", "<=", "="}
MAX_WINDOW = 60
MIN_AGE, MAX_AGE = 0, 120


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    k_threshold: int
    privacy_budget_remaining: float
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "k_threshold": self.k_threshold,
            "privacy_budget_remaining": self.privacy_budget_remaining,
            **self.details,
        }


def evaluate_policy(
    *,
    role: str,
    spec: dict[str, Any],
    k_threshold: int,
    budget_remaining: float,
    requested_epsilon: float | None,
    historical_count: int = 0,
) -> PolicyDecision:
    requested = {str(f).lower() for f in (spec.get("requested_fields") or [])}
    bad = requested & FORBIDDEN_FIELDS
    if bad:
        return PolicyDecision(
            False,
            "Raw patient-level data is prohibited.",
            k_threshold,
            budget_remaining,
            {"denied_fields": sorted(bad)},
        )

    if spec.get("aggregation", "count_distinct_patients") not in ALLOWED_AGG:
        return PolicyDecision(False, "Only count-level aggregation is permitted.", k_threshold, budget_remaining)

    if role in ("auditor",):
        return PolicyDecision(False, "Role auditor cannot execute clinical queries.", k_threshold, budget_remaining)

    if role not in ("researcher", "clinician", "admin"):
        return PolicyDecision(False, f"Role {role} is not authorized to query.", k_threshold, budget_remaining)

    age_min = int(spec.get("age_min", 0))
    age_max = int(spec.get("age_max", 120))
    if age_min < MIN_AGE or age_max > MAX_AGE or age_min > age_max:
        return PolicyDecision(False, "Age range is invalid.", k_threshold, budget_remaining)

    window = int(spec.get("window_months") or 12)
    if window < 1 or window > MAX_WINDOW:
        return PolicyDecision(False, f"Time range must be 1–{MAX_WINDOW} months.", k_threshold, budget_remaining)

    op = spec.get("lab_op") or ">"
    if op not in ALLOWED_LAB_OPS:
        return PolicyDecision(False, "Unsupported lab comparison operator.", k_threshold, budget_remaining)

    if spec.get("return_rows") or spec.get("row_level"):
        return PolicyDecision(False, "Raw patient-level data is prohibited.", k_threshold, budget_remaining)

    if requested_epsilon is not None:
        if requested_epsilon <= 0 or requested_epsilon > 20:
            return PolicyDecision(False, "epsilon must be in (0, 20].", k_threshold, budget_remaining)
        if requested_epsilon > budget_remaining + 1e-9:
            return PolicyDecision(
                False,
                f"Insufficient privacy budget (need {requested_epsilon}, remaining {budget_remaining:.3f}).",
                k_threshold,
                budget_remaining,
            )

    return PolicyDecision(
        True,
        "Query satisfies institutional privacy policy",
        k_threshold,
        budget_remaining,
        {
            "historical_queries": historical_count,
            "aggregation": spec.get("aggregation", "count_distinct_patients"),
        },
    )
