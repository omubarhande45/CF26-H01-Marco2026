# Deployment

## Local (no Docker)

```bash
cd /home/user/fcqf
python3 institutional_nodes/generate_data.py
# terminals:
NODE_ID=hospital_a NODE_NAME="Hospital A" uvicorn institutional_nodes.node_app:app --host 0.0.0.0 --port 8101
NODE_ID=hospital_b NODE_NAME="Hospital B" DB_PATH=institutional_nodes/data/hospital_b.db uvicorn institutional_nodes.node_app:app --host 0.0.0.0 --port 8102
NODE_ID=diagnostic_lab NODE_NAME="Diagnostic Laboratory" DB_PATH=institutional_nodes/data/diagnostic_lab.db uvicorn institutional_nodes.node_app:app --host 0.0.0.0 --port 8103
uvicorn gateway.app:app --host 0.0.0.0 --port 8080
cd frontend && npm install && npm run dev
```

## Docker

```bash
python3 institutional_nodes/generate_data.py
docker compose up --build
```

Gateway :8080, frontend :5173, nodes :8101–8103.
