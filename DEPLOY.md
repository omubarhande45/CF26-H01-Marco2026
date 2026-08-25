# FCQF deploy structure

```
Vercel (UI only)                  Docker host (API + data)
┌─────────────────────┐           ┌──────────────────────────────────┐
│  *.vercel.app       │  /api/*   │  web :80  nginx → /api → gateway │
│  React static +     │ ────────► │  gateway :8080                   │
│  serverless proxy   │ GATEWAY_  │    ├─ hospital_a :8101           │
│  if GATEWAY_URL set │ URL       │    ├─ hospital_b :8102           │
└─────────────────────┘           │    └─ diagnostic_lab :8103       │
                                  └──────────────────────────────────┘
```

Do **not** put nodes or SQLite on Vercel.

---

## Vercel (UI only — do not choose FastAPI)

Vercel’s import wizard may suggest **FastAPI** because of `requirements.txt`. **Do not use FastAPI.** This site is a **Vite React** app.

**Import settings**

| Field | Value |
|--------|--------|
| Framework | **Vite** (or Other). Never FastAPI |
| Root Directory | `frontend` **or** leave empty (repo root) |
| Build | `npm run build` (if root = `frontend`) |
| Output | `dist` (if root = `frontend`) |
| Env | `GATEWAY_URL` = `https://YOUR-APP.up.railway.app` |

If Root Directory is empty, root `vercel.json` already sets Vite + `frontend/dist`.

After import: **Settings → Environment Variables → `GATEWAY_URL`** → Redeploy.

Railway failed before because there was **no root Dockerfile** and Nixpacks did not know how to start four processes.

This repo now has:

- `Dockerfile` — builds data + Python deps
- `deploy/railway_start.sh` — Hospital A/B + Lab on localhost, gateway on `$PORT`
- `railway.toml` — tells Railway to use that Dockerfile

**In Railway**

1. Open the failed service → **Settings**
2. Builder: **Dockerfile** (or leave default; `railway.toml` sets it)
3. Variables (optional but recommended):
   - `JWT_SECRET` = long random string
   - `ALLOW_DEMO_USERS` = `1` (required for researcher / research123)
   - `ALLOWED_ORIGINS` = `https://cf-26-h01-marco2026-one.vercel.app`
   - Leave `FCQF_ENV` unset (defaults to `development` so the image boots even without JWT_SECRET)
4. **Generate domain** (Settings → Networking → Public domain)
5. Redeploy (push to `main` or Deploy → Redeploy)
6. Open `https://YOUR-SERVICE.up.railway.app/health`
7. Vercel env `GATEWAY_URL` = that URL (no trailing slash) → Redeploy Vercel

Nodes are **not** public; only the gateway port Railway assigns is public.

From the **repo root**:

```bash
cp deploy/.env.example .env
# edit JWT_SECRET

docker compose -f deploy/docker-compose.yml up -d --build
```

| URL | Service |
|-----|---------|
| http://localhost | UI (nginx) — **use this to log in** |
| http://localhost:8080 | Gateway HTML + `/docs` |
| http://localhost:8080/health | `{"ok":true}` |

Sign in: `researcher` / `research123`.

Stop:

```bash
docker compose -f deploy/docker-compose.yml down
```

---

## 2. Vercel UI + Docker API (your current site)

### A. Run the API somewhere public

Same compose on a cloud VM (DigitalOcean, Lightsail, EC2) **or** Railway/Render using `deploy/Dockerfile.app`.

Open `http://YOUR-SERVER:8080/health` — must return JSON ok.

### B. Point Vercel at it

1. Vercel → project → **Settings → Environment Variables**
2. `GATEWAY_URL` = `http://YOUR-SERVER:8080` (or `https://…` if you added TLS)
3. **Redeploy**

Login on `https://cf-26-h01-marco2026-one.vercel.app` then works because `/api/auth/login` is proxied to the gateway.

On the gateway `.env`:

```
ALLOWED_ORIGINS=https://cf-26-h01-marco2026-one.vercel.app
```

---

## 3. Vercel project settings

| Setting | Value |
|---------|--------|
| Root Directory | *(empty — repo root)* |
| Build | `npm run build --prefix frontend` |
| Output | `frontend/dist` |
| Env | `GATEWAY_URL` = public gateway |

Files that make this work:

- `vercel.json` — SPA rewrite  
- `api/[...path].js` — `/api` → `GATEWAY_URL`  
- `frontend/vercel.json` — if Root Directory is `frontend`

---

## 4. What each folder is for

| Path | Role |
|------|------|
| `deploy/Dockerfile.app` | Python image (gateway + nodes + data) |
| `deploy/Dockerfile.web` | Nginx + built React |
| `deploy/docker-compose.yml` | Full stack |
| `deploy/nginx.conf` | `/api` → gateway, SPA fallback |
| `deploy/.env.example` | Secrets template |
| `gateway/` | Coordinator API |
| `institutional_nodes/` | Hospital A/B + Lab |
| `frontend/` | Dashboard |
| `api/` | Vercel proxy only |

---

## 5. Ports (never expose nodes to the internet)

| Port | Bind | Public? |
|------|------|---------|
| 80 | web | yes |
| 8080 | gateway | yes (or only via nginx `/api`) |
| 8101–8103 | nodes | **no** — Docker internal only |

---

## 6. Health checks

```bash
curl -s http://localhost/api/health
curl -s -X POST http://localhost/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"researcher","password":"research123"}'
```

A token in the JSON means deploy is correct.
