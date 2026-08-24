"""Query lifecycle state machine. Invalid transitions are rejected."""
from __future__ import annotations

TERMINAL = {"COMPLETED", "PARTIAL", "SUPPRESSED", "DENIED", "FAILED", "TIMEOUT", "CANCELLED"}

TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"VALIDATING", "DENIED", "CANCELLED"},
    "VALIDATING": {"PLANNING", "DENIED", "CANCELLED"},
    "PLANNING": {"DISPATCHING", "DENIED", "FAILED", "CANCELLED"},
    "DISPATCHING": {"RUNNING", "FAILED", "CANCELLED", "TIMEOUT"},
    "RUNNING": {"AGGREGATING", "PARTIAL", "FAILED", "TIMEOUT", "CANCELLED"},
    "AGGREGATING": {"PRIVACY_CHECK", "FAILED", "CANCELLED"},
    "PRIVACY_CHECK": {"COMPLETED", "PARTIAL", "SUPPRESSED", "FAILED", "CANCELLED"},
    "COMPLETED": set(),
    "PARTIAL": set(),
    "SUPPRESSED": set(),
    "DENIED": set(),
    "FAILED": set(),
    "TIMEOUT": set(),
    "CANCELLED": set(),
}


class InvalidTransition(ValueError):
    pass


def advance(current: str, nxt: str) -> str:
    if nxt not in TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"cannot go from {current} to {nxt}")
    return nxt
