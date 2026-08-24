#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
set -a
[ -f .env ] && source .env
set +a
python3 institutional_nodes/generate_data.py --patients "${PATIENTS:-10000}" --seed "${SEED:-42}" >/dev/null
mkdir -p /tmp/fcqf-logs
NODE_ID=hospital_a NODE_NAME="Hospital A" DB_PATH="$ROOT/institutional_nodes/data/hospital_a.db" \
  uvicorn institutional_nodes.node_app:app --host 0.0.0.0 --port 8101 >/tmp/fcqf-logs/a.log 2>&1 &
echo $! >/tmp/fcqf-logs/a.pid
NODE_ID=hospital_b NODE_NAME="Hospital B" DB_PATH="$ROOT/institutional_nodes/data/hospital_b.db" \
  uvicorn institutional_nodes.node_app:app --host 0.0.0.0 --port 8102 >/tmp/fcqf-logs/b.log 2>&1 &
echo $! >/tmp/fcqf-logs/b.pid
NODE_ID=diagnostic_lab NODE_NAME="Diagnostic Laboratory" DB_PATH="$ROOT/institutional_nodes/data/diagnostic_lab.db" \
  uvicorn institutional_nodes.node_app:app --host 0.0.0.0 --port 8103 >/tmp/fcqf-logs/l.log 2>&1 &
echo $! >/tmp/fcqf-logs/l.pid
uvicorn gateway.app:app --host 0.0.0.0 --port 8080 >/tmp/fcqf-logs/gw.log 2>&1 &
echo $! >/tmp/fcqf-logs/gw.pid
(cd frontend && npm run dev) >/tmp/fcqf-logs/fe.log 2>&1 &
echo $! >/tmp/fcqf-logs/fe.pid
echo "started 8101 8102 8103 8080 5173"
