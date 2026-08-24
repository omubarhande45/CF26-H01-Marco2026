"""Unit tests for policy + DP (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from privacy.dp import DPError, LaplaceMechanism, PrivacyBudgetLedger, validate_epsilon
from privacy.policy import evaluate_policy


def test_epsilon_validation():
    validate_epsilon(1.0)
    try:
        validate_epsilon(0)
        raise AssertionError("expected fail")
    except DPError:
        pass
    try:
        validate_epsilon(-1)
        raise AssertionError("expected fail")
    except DPError:
        pass


def test_laplace_changes_count():
    mech = LaplaceMechanism()
    noisy = [mech.protect_count(100, 0.5) for _ in range(8)]
    assert any(v != 100 for v in noisy)
    assert all(v >= 0 for v in noisy)


def test_budget_exhaustion():
    led = PrivacyBudgetLedger(default_budget=1.0)
    led.consume("researcher", "hospital_a", 0.8)
    try:
        led.consume("researcher", "hospital_a", 0.5)
        raise AssertionError("should exhaust")
    except DPError:
        pass
    assert led.remaining("researcher", "hospital_a") < 0.3


def test_policy_denies_raw_fields():
    d = evaluate_policy(
        role="researcher",
        spec={"requested_fields": ["patient_id", "name", "phone", "address"], "age_min": 40, "age_max": 70},
        k_threshold=10,
        budget_remaining=8,
        requested_epsilon=None,
    )
    assert d.allowed is False
    assert "prohibited" in d.reason.lower()


def test_policy_allows_valid():
    d = evaluate_policy(
        role="researcher",
        spec={
            "age_min": 40,
            "age_max": 70,
            "conditions": ["Type 2 Diabetes"],
            "aggregation": "count_distinct_patients",
            "window_months": 12,
        },
        k_threshold=10,
        budget_remaining=8,
        requested_epsilon=1.0,
    )
    assert d.allowed is True


def test_auditor_cannot_query():
    d = evaluate_policy(
        role="auditor",
        spec={"age_min": 40, "age_max": 70},
        k_threshold=10,
        budget_remaining=8,
        requested_epsilon=None,
    )
    assert d.allowed is False


if __name__ == "__main__":
    test_epsilon_validation()
    test_laplace_changes_count()
    test_budget_exhaustion()
    test_policy_denies_raw_fields()
    test_policy_allows_valid()
    test_auditor_cannot_query()
    print("unit ok")
