# Railway / single-service image: 3 nodes (localhost) + gateway on $PORT
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
COPY deploy/railway_start.sh /app/deploy/railway_start.sh

RUN chmod +x /app/deploy/railway_start.sh \
 && python3 institutional_nodes/generate_data.py --patients 4000 \
 && python3 scripts/load_epidemiology.py

ENV NODE_A=http://127.0.0.1:8101 \
    NODE_B=http://127.0.0.1:8102 \
    NODE_L=http://127.0.0.1:8103 \
    ALLOW_DEMO_USERS=1 \
    FCQF_ENV=production

EXPOSE 8080
CMD ["/app/deploy/railway_start.sh"]
