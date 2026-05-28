# Breathe ESG — Emissions Data Ingestion & Review

Ingests emissions/activity data from three real-world source types (SAP fuel &
procurement, electricity utility exports, corporate travel), normalizes it into
a single audited data model, and gives analysts a dashboard to review, flag,
and sign off rows before they are locked for auditors.

## Stack

- **Backend:** Django + Django REST Framework, PostgreSQL (SQLite for local dev),
  SimpleJWT auth, Celery + Redis for background ingestion, Pandas for source
  normalization, openpyxl for XLSX export
- **Frontend:** React + Vite + Tailwind, React Router, TanStack Query,
  TanStack Table, Recharts, axios

## Layout

```
backend/   Django project (config/) + responsibility-scoped apps (apps/)
frontend/  Vite React app, feature-based (src/features/*)
docker-compose.yml  db + redis + backend + worker + frontend
```

Apps are split by responsibility (`tenants`, `reference`, `ingestion`,
`emissions`, `review`, `audit`), and all source-specific logic is isolated
in `apps/ingestion/adapters/`.

## Run locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo    # seeds an org, user, and sample batches
python manage.py runserver
```

Default demo credentials: **`admin` / `admin12345`**.

### Frontend

```powershell
cd frontend
npm install
npm run dev    # http://localhost:5173 (proxies /api → :8000)
```

### Full stack via Docker

```powershell
docker compose up
```

Brings up Postgres, Redis, the Django backend, a Celery worker, and the
frontend (served by nginx).

### Celery worker (manual)

For local async ingestion outside Docker:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
celery -A config worker -l info
```

In dev, `CELERY_TASK_ALWAYS_EAGER=True` by default so uploads run inline; set
`CELERY_TASK_ALWAYS_EAGER=False` and start the worker to exercise the async path.

## Authentication

JWT (`djangorestframework-simplejwt`). Flow:

| Step | Endpoint | Body | Returns |
| --- | --- | --- | --- |
| Login | `POST /api/v1/tenants/auth/login/` | `{username, password}` | `{access, refresh, user, organizations}` |
| Refresh | `POST /api/v1/tenants/auth/refresh/` | `{refresh}` | `{access[, refresh]}` (rotated) |
| Me | `GET /api/v1/tenants/auth/me/` | – | `{user, organizations}` |

SPA requests carry `Authorization: Bearer <access>` and `X-Organization: <id>`.
The axios client transparently refreshes on 401 and retries the original request.

## Exporting data

Auditor handoff: `GET /api/v1/emissions/activities/export/?format=csv|xlsx`.
Filters from the activities list apply (`scope`, `activity_category`, `batch`,
`site_code`), so an analyst can export exactly what they see.

## Data quality score

Each `ActivityRecord` serializer includes `data_quality_score` (0.0–1.0),
computed from the row's unresolved anomaly flags. See
[backend/apps/emissions/serializers.py](backend/apps/emissions/serializers.py)
for the weights.

## Deployment

| Service | Target | Notes |
| --- | --- | --- |
| Frontend | Vercel | `frontend/` as project root, build command `npm run build`, output `dist/`. Set `VITE_API_BASE_URL` to your API origin. |
| Backend | Render / Railway / Fly | Uses `backend/Dockerfile`. Provide `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`. |
| Worker | same platform, separate service | `celery -A config worker -l info`. Shares env with the backend. |
| Database | Managed Postgres (Render/Neon/Supabase) | Set `DATABASE_URL`. |
| Cache / broker | Managed Redis (Upstash, Render) | Set both Celery URLs. |

## Deliverable docs

- [MODEL.md](MODEL.md) — data model and rationale
- [DECISIONS.md](DECISIONS.md) — ambiguities resolved + open questions for the PM
- [TRADEOFFS.md](TRADEOFFS.md) — what was deliberately not built
- [SOURCES.md](SOURCES.md) — per-source research, sample data, and failure modes
