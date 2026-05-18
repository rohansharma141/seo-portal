# Building10X SEO Portal

Standalone web portal + REST API for automated SEO auditing of websites.
Built for Kedar Estate and PropOS, with a token-authenticated API so PropOS
can audit broker-generated landing pages programmatically.

- **Backend** — FastAPI (Python 3.12), async SQLAlchemy 2.0 + Supabase
  (Postgres), APScheduler, JWT / API-token auth.
- **Frontend** — Next.js 14 (App Router) + TypeScript + Tailwind.
- Works **fully on mock data** with zero credentials — every external
  integration (Firecrawl, GSC, Claude, Resend, DataForSEO) is a placeholder
  that returns realistically-shaped mock data until a key is set.

Built per `docs/SEO_PORTAL_BUILD_DOC.md` (+ `SEO_PORTAL_ADDENDUM_v1.1.md`).
API reference: `docs/API_USAGE.md`; schema: `docs/openapi.json`.

---

## Repository layout

```
backend/    FastAPI app, SEO rules engine, audit pipeline, scheduler, tests
frontend/   Next.js 14 portal UI
docs/        Build spec, API usage, OpenAPI schema
```

## Prerequisites

- Python 3.12, Node.js 20+ / npm
- (Optional) A Supabase/Postgres database — the API boots and serves
  `/health` and all mock-data flows without one; only DB-backed endpoints
  need it.

---

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux

copy .env.example .env        # then edit (all keys optional — empty = mock)
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs> · ReDoc: `/redoc`
- Run tests: `.\.venv\Scripts\python.exe -m pytest` (64 passing)

**Database (when you have Supabase/Postgres):** set `DATABASE_URL`, then
apply the schema with either:

```bash
.\.venv\Scripts\python.exe -m alembic upgrade head     # revisions 0001, 0002
# or paste backend/migrations/001_initial_schema.sql + 002_audits_metadata.sql
# into the Supabase SQL editor
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                    # http://localhost:3000
```

---

## Environment variables

All backend vars live in `backend/.env.example` (Section 10 of the build
doc). **Every integration key is optional** — leave it empty to run on mock
data; the portal stays fully functional.

| Group | Vars | Empty behaviour |
|---|---|---|
| Database | `SUPABASE_URL`, `SUPABASE_KEY`, `DATABASE_URL` | DB endpoints error; mock flows work |
| Auth | `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` | dev default secret |
| Crawl | `FIRECRAWL_API_KEY` | mock crawl (3 sample pages) |
| Search Console | `GSC_CREDENTIALS_PATH`, `GSC_SITE_URL` | mock GSC snapshot |
| AI analysis | `ANTHROPIC_API_KEY` | mock analysis (Haiku 4.5 target) |
| Email | `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `NOTIFICATION_EMAIL` | no email sent |
| Backlinks | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` | mock placeholder (Addendum v1.1) |
| App | `ENVIRONMENT`, `APP_URL`, `FRONTEND_URL`, `API_TOKEN_PREFIX`, `LOG_LEVEL`, `SCHEDULER_ENABLED` | sensible defaults |

Frontend: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_APP_NAME`,
`NEXT_PUBLIC_API_TOKEN` (dev bearer fallback).

---

## Trigger your first audit

With the backend running (mock mode is fine):

```bash
BASE=http://localhost:8000

# 1. Mint an admin JWT (dev only — portal normally uses Supabase Auth)
cd backend
.\.venv\Scripts\python.exe -c "from middleware.auth import create_access_token; print(create_access_token('admin'))"
export TOKEN=<paste the JWT>

# 2. Register a site
SITE=$(curl -s -X POST $BASE/api/v1/sites -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Kedar Estate","domain":"kedar.estate","url":"https://kedar.estate","site_type":"brokerage"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 3. Trigger an audit and poll
AUDIT=$(curl -s -X POST $BASE/api/v1/audits -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d "{\"site_id\":\"$SITE\"}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['audit_id'])")

curl -s $BASE/api/v1/audits/$AUDIT/status -H "Authorization: Bearer $TOKEN"
curl -s $BASE/api/v1/audits/$AUDIT -H "Authorization: Bearer $TOKEN"
```

On mock data this yields an overall score of ~87. Or just use the portal
UI: **Sites → Add New Site → Audit Now**. See `docs/API_USAGE.md` for every
endpoint.

---

## Connecting the real integrations

Each integration swaps from mock to real **purely by setting its env
var(s)** and restarting the backend — no code change:

| Integration | Set | Get a key |
|---|---|---|
| Firecrawl (crawl) | `FIRECRAWL_API_KEY` | firecrawl.dev |
| Google Search Console | `GSC_CREDENTIALS_PATH`, `GSC_SITE_URL` | service-account JSON |
| Claude (AI analysis) | `ANTHROPIC_API_KEY` | console.anthropic.com |
| Resend (email) | `RESEND_API_KEY` | resend.com |
| DataForSEO (backlinks) | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` | dataforseo.com |

> The real HTTP calls for each integration are stubbed with a clear
> `NotImplementedError("[PLACEHOLDER] …")` and a commented implementation
> outline at the call site — wire them in when the keys are provisioned.

The Settings page in the portal lists each integration and the env var to
set.

---

## Architecture notes

- **SEO engine** (`backend/utils/seo_rules.py`, `services/scorer.py`) is
  pure Python, no external deps — 28 rules, weighted scoring
  (technical 30 / content 25 / E-E-A-T 20 / performance 15 / structure 10).
- **Audit pipeline** (`services/audit_pipeline.py`) runs as a FastAPI
  background task: crawl → rules → score → AI analysis → backlinks →
  persist → fire signed webhooks.
- **Persistence** is behind a repository interface; tests use an in-memory
  fake (no DB needed) — `pytest` is fully green offline.
- **Scheduler** (`services/scheduler.py`): weekly (Mon 06:00 UTC) and
  monthly (1st 07:00 UTC) audits of active sites.

## Known limitations

- Real Postgres/Supabase round-trip is **unverified** (no creds during
  build); the ORM, raw SQL and Alembic migrations are written and checked
  offline. Run `alembic upgrade head` against a real DB to validate.
- `frontend` is pinned to Next.js **14.2.35** (latest 14.x). Residual
  `npm audit` highs are fixed only in Next 15 — upgrading is a deliberate
  major-version decision, intentionally out of scope here.
- No login UI (portal auth is Supabase Auth, external); the frontend reads
  a bearer token from `localStorage` / `NEXT_PUBLIC_API_TOKEN`.

## Deployment targets

Backend → Hetzner (Dockerfile included) · Frontend → Vercel ·
DNS/CDN → Cloudflare · Monitoring → BetterStack.
