"""In-process counters for /metrics (Prometheus text format). No PHI."""
from __future__ import annotations

import threading
import time
from collections import defaultdict

_lock = threading.Lock()
_counters: dict[str, float] = defaultdict(float)
_hist: dict[str, list[float]] = defaultdict(list)


def inc(name: str, n: float = 1.0):
    with _lock:
        _counters[name] += n


def observe(name: str, value: float):
    with _lock:
        _hist[name].append(value)
        _counters[name + "_sum"] += value
        _counters[name + "_count"] += 1


def render() -> str:
    lines = ["# HELP fcqf_info FCQF coordinator metrics", "# TYPE fcqf_info gauge", f"fcqf_info {time.time()}"]
    with _lock:
        for k, v in sorted(_counters.items()):
            lines.append(f"{k} {v}")
    return "\n".join(lines) + "\n"
