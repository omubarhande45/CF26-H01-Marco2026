#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
curl -sf http://127.0.0.1:8101/health >/dev/null && echo "Hospital A: up"
curl -sf http://127.0.0.1:8102/health >/dev/null && echo "Hospital B: up"
curl -sf http://127.0.0.1:8103/health >/dev/null && echo "Lab: up"
curl -sf http://127.0.0.1:8080/health >/dev/null && echo "Gateway: up"
python3 tests/test_unit_privacy.py
python3 tests/test_federation.py
python3 tests/test_phase13.py
python3 tests/test_end_to_end.py
echo verify_ok
