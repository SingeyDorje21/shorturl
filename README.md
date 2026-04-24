# Short URL — Microservice Architecture

A production-grade URL shortener split into four focused services.

```
┌──────────────────────────────────────────────────────────┐
│                   Public Internet                        │
└───────────────────────┬──────────────────────────────────┘
                        │ :8000
              ┌─────────▼─────────┐
              │   API Gateway     │  CORS · routing · proxy
              └────┬─────────┬────┘
                   │         │
          :8001    │         │ :8002
    ┌──────────────▼──┐  ┌───▼──────────────┐
    │  Shortener Svc  │  │  Redirect Svc    │
    │  POST /shorten  │  │  GET /{code}     │
    │  GET /{code}/info│  │  (hot path)      │
    └──────────────┬──┘  └───┬──────────────┘
                   │         │
              ┌────▼─────────▼────┐
              │   Shared SQLite   │  (swap for Postgres in prod)
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │   Cleanup Svc     │  :8003
              │  background task  │  deletes expired URLs hourly
              └───────────────────┘
```

## Services

| Service    | Port | Responsibility |
|------------|------|----------------|
| `gateway`  | 8000 | Public entry point. CORS, auth hooks, proxies to internal services |
| `shortener`| 8001 | `POST /shorten`, `GET /{code}/info`. Writes to DB |
| `redirect` | 8002 | `GET /{code}` → 307 redirect. Read-heavy hot path |
| `cleanup`  | 8003 | Background worker — purges expired/inactive rows on a schedule |

## Bugs fixed from the original codebase

1. **SQLite pool args crash** — `pool_size`/`max_overflow` are now only passed for non-SQLite engines
2. **Naive/aware datetime mismatch** — all datetimes are stored and compared as UTC; SQLite naive values are normalised on read-back
3. **`active_duration_days` silently ignored for ≤ 30** — now any valid value is honoured (capped at `URL_ACTIVE_DAYS_MAX`)
4. **Missing CORS middleware** — CORS now lives in the gateway (the right place)
5. **Route ordering: `/shorten` and `/health` swallowed by `/{short_code}`** — fixed by registering specific routes before wildcard ones
6. **`delete_outdated.py` was empty** — replaced by the full Cleanup service with a configurable scheduler and a manual `/run` trigger
7. **Pydantic v2 deprecations** — migrated to `model_config = ConfigDict(...)`

## Quickstart (local, no Docker)

```bash
# 1. Clone and enter the repo
git clone <your-repo> && cd shorturl

# 2. Copy env template
cp .env.example .env

# 3. Start all four services (installs deps automatically)
bash run_dev.sh
```

Services will be available at:
- Gateway (public): http://localhost:8000/docs
- Shortener (internal): http://localhost:8001/docs
- Redirect (internal): http://localhost:8002/docs
- Cleanup (internal): http://localhost:8003/docs

## Quickstart (Docker)

```bash
docker-compose up --build
```

## API

All requests go through the **gateway** on port 8000.

### Shorten a URL
```
POST /shorten
Content-Type: application/json

{ "original_url": "https://example.com", "active_duration_days": 7 }
```

Response:
```json
{
  "original_url": "https://example.com/",
  "short_code": "4mQkZ7",
  "is_active": true,
  "clicks": 0,
  "short_url": "http://localhost:8000/4mQkZ7",
  "active_till": "2026-04-30T10:00:00Z"
}
```

### Follow a short URL
```
GET /{short_code}          → 307 redirect to original URL
```

### Get stats
```
GET /{short_code}/info     → URL metadata (clicks, expiry, etc.)
```

### Manually trigger cleanup
```
POST http://localhost:8003/run   → {"deleted": 3, "ran_at": "..."}
```

## Running tests

```bash
# From repo root
PYTHONPATH=. pytest tests/ -v
```

## Switching to Postgres (production)

1. Change `DATABASE_URL` in your `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/shorturl
   ```
2. Add `asyncpg` to each service's `requirements.txt`
3. Run `alembic upgrade head` (or let `init_db()` create tables on startup)

## Project structure

```
shorturl/
├── shared/                  # Shared library (models, schemas, config, services)
│   └── app/
│       ├── config.py
│       ├── db/
│       │   ├── __init__.py  (Base)
│       │   ├── models.py
│       │   └── session.py
│       ├── schemas/
│       │   └── __init__.py
│       └── services/
│           └── __init__.py  (base62 encoder)
├── gateway/                 # API gateway
│   ├── app/main.py
│   ├── Dockerfile
│   └── requirements.txt
├── shortener/               # URL creation + stats
│   ├── app/
│   │   ├── main.py
│   │   └── routes.py
│   ├── Dockerfile
│   └── requirements.txt
├── redirect/                # Hot-path redirect
│   ├── app/
│   │   ├── main.py
│   │   └── routes.py
│   ├── Dockerfile
│   └── requirements.txt
├── cleanup/                 # Background expiry worker
│   ├── app/main.py
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   ├── conftest.py
│   ├── test_shared.py
│   ├── test_shortener.py
│   └── test_redirect.py
├── docker-compose.yml
├── run_dev.sh
├── pytest.ini
└── .env.example
```
