# Shared image: gateway + institutional nodes
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY gateway ./gateway
COPY institutional_nodes ./institutional_nodes
COPY institutions ./institutions
COPY privacy ./privacy
COPY schema_mapper ./schema_mapper
COPY shared ./shared
COPY scripts ./scripts
COPY data ./data

RUN python3 institutional_nodes/generate_data.py \
 && python3 scripts/load_epidemiology.py

EXPOSE 8080 8101 8102 8103
CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8080"]
