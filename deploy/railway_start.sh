#!/bin/sh
set -eu

export NODE_A="${NODE_A:-http://127.0.0.1:8101}"
export NODE_B="${NODE_B:-http://127.0.0.1:8102}"
export NODE_L="${NODE_L:-http://127.0.0.1:8103}"
export ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-*}"
export FCQF_ENV="${FCQF_ENV:-development}"
export ALLOW_DEMO_USERS="${ALLOW_DEMO_USERS:-1}"
if [ -z "${JWT_SECRET:-}" ]; then
  export JWT_SECRET="fcqf-dev-secret-change-me"
fi

echo "starting Hospital A :8101"
NODE_ID=hospital_a NODE_NAME="Hospital A" \
  DB_PATH=/app/institutional_nodes/data/hospital_a.db \
  uvicorn institutional_nodes.node_app:app --host 127.0.0.1 --port 8101 &

echo "starting Hospital B :8102"
NODE_ID=hospital_b NODE_NAME="Hospital B" \
  DB_PATH=/app/institutional_nodes/data/hospital_b.db \
  uvicorn institutional_nodes.node_app:app --host 127.0.0.1 --port 8102 &

echo "starting Diagnostic Lab :8103"
NODE_ID=diagnostic_lab NODE_NAME="Diagnostic Laboratory" \
  DB_PATH=/app/institutional_nodes/data/diagnostic_lab.db \
  uvicorn institutional_nodes.node_app:app --host 127.0.0.1 --port 8103 &

# wait until nodes accept connections
python3 - <<'PY'
import time, urllib.request
for port in (8101, 8102, 8103):
    url = f"http://127.0.0.1:{port}/health"
    for _ in range(60):
        try:
            urllib.request.urlopen(url, timeout=1)
            print("ready", url)
            break
        except Exception:
            time.sleep(0.4)
    else:
        raise SystemExit(f"node on {port} did not start")
PY

PORT="${PORT:-8080}"
echo "starting gateway on 0.0.0.0:${PORT}"
exec uvicorn gateway.app:app --host 0.0.0.0 --port "${PORT}"
