# Local Development

## Prerequisites

- Python 3.11+ installed
- [uv](https://docs.astral.sh/uv/) installed (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker + Docker Compose installed
- Git

## First-Time Setup

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd indian-financial-news-aggregator
```

### 2. Copy environment config

```bash
cp .env.example .env
```

For local development (backend outside Docker, DB inside Docker), change:
```
POSTGRES_HOST=localhost
```

### 3. Start PostgreSQL

```bash
docker compose up db -d
```

### 4. Install Python dependencies

```bash
cd backend
uv sync
```

### 5. Run the backend

```bash
uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Verify

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### 7. Seed default feeds (after models are implemented)

```bash
uv run python scripts/seed_feeds.py
```

### 8. Trigger first pipeline run

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run
```

## Day-to-Day Workflow

```bash
# Terminal 1: PostgreSQL
docker compose up db

# Terminal 2: Backend with hot reload
cd backend
uv run uvicorn src.app.main:app --reload

# Terminal 3: testing
cd backend
uv run pytest tests/ -v
```

## Environment Variables

See [.env.example](../../.env.example) for all available variables with descriptions.

Key overrides for local development:
| Variable | Docker Value | Local Dev Value |
|----------|-------------|----------------|
| `POSTGRES_HOST` | `db` | `localhost` |
| `LOG_LEVEL` | `INFO` | `DEBUG` |
| `APP_ENV` | `production` | `development` |

## Common Issues

| Issue | Solution |
|-------|----------|
| `asyncpg.CannotConnectNowError` | PostgreSQL not ready. Wait a few seconds or check `docker compose ps` |
| `ModuleNotFoundError` | Run `uv sync` from `backend/` directory |
| Port 5432 already in use | Another PostgreSQL instance running. Stop it or change `POSTGRES_PORT` |
| Port 8000 already in use | Another process on 8000. Kill it or change `BACKEND_PORT` |
