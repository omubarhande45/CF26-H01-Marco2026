"""Laplace differential privacy for aggregate counts only."""
from __future__ import annotations

import math
import random
import threading
from dataclasses import dataclass, field


class DPError(ValueError):
    pass


def validate_epsilon(epsilon: float) -> float:
    if epsilon is None or not math.isfinite(epsilon) or epsilon <= 0 or epsilon > 20:
        raise DPError("epsilon must be in (0, 20]")
    return float(epsilon)


def validate_delta(delta: float) -> float:
    if delta < 0 or delta >= 1:
        raise DPError("delta must be in [0, 1)")
    return float(delta)


class LaplaceMechanism:
    """Add Laplace noise to a numeric aggregate. Sensitivity defaults to 1 (count)."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def noise(self, epsilon: float, sensitivity: float = 1.0) -> float:
        eps = validate_epsilon(epsilon)
        if sensitivity <= 0:
            raise DPError("sensitivity must be > 0")
        scale = sensitivity / eps
        # Inverse CDF of Laplace(0, b)
        u = self.rng.random() - 0.5
        return -scale * math.copysign(1.0, u) * math.log(1 - 2 * abs(u))

    def protect_count(self, exact: int, epsilon: float) -> int:
        noisy = exact + self.noise(epsilon, 1.0)
        return max(0, int(round(noisy)))


@dataclass
class BudgetAccount:
    actor: str
    institution: str
    remaining: float
    consumed: float = 0.0
    queries: int = 0


class PrivacyBudgetLedger:
    """Track ε spend per (actor, institution). Repeated queries always consume budget."""

    def __init__(self, default_budget: float = 8.0):
        self.default_budget = default_budget
        self._lock = threading.Lock()
        self._accounts: dict[tuple[str, str], BudgetAccount] = {}

    def remaining(self, actor: str, institution: str) -> float:
        with self._lock:
            acc = self._accounts.get((actor, institution))
            return acc.remaining if acc else self.default_budget

    def snapshot(self, actor: str) -> dict[str, float]:
        with self._lock:
            out = {}
            for (a, inst), acc in self._accounts.items():
                if a == actor:
                    out[inst] = acc.remaining
            return out

    def consume(self, actor: str, institution: str, epsilon: float) -> BudgetAccount:
        eps = validate_epsilon(epsilon)
        with self._lock:
            key = (actor, institution)
            acc = self._accounts.get(key)
            if acc is None:
                acc = BudgetAccount(actor=actor, institution=institution, remaining=self.default_budget)
                self._accounts[key] = acc
            if acc.remaining < eps:
                raise DPError(
                    f"privacy budget exhausted for {actor}@{institution}: "
                    f"need {eps}, remaining {acc.remaining:.3f}"
                )
            acc.remaining = round(acc.remaining - eps, 6)
            acc.consumed = round(acc.consumed + eps, 6)
            acc.queries += 1
            return acc
