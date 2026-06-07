# Deployment Architecture

## Current: Docker Compose (Single Host)

```
┌─────────────────────────────────────────┐
│              Docker Host                 │
│                                          │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │ finnews-     │  │ finnews-db      │  │
│  │ backend      │  │                 │  │
│  │              │  │ PostgreSQL 16   │  │
│  │ Python 3.12  │  │ Alpine          │  │
│  │ FastAPI      │──▶│                 │  │
│  │ Uvicorn      │  │ Vol: postgres_  │  │
│  │ Port: 8000   │  │       data      │  │
│  └──────────────┘  └─────────────────┘  │
│        │                    │            │
└────────┼────────────────────┼────────────┘
         │                    │
    host:8000           host:5432
```

## Container Details

### finnews-backend

| Property | Value |
|----------|-------|
| Base image | `python:3.12-slim` |
| Package manager | uv (copied from `ghcr.io/astral-sh/uv:latest`) |
| Entry point | `uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000` |
| Exposed port | 8000 |
| Restart policy | `unless-stopped` |
| Env source | `.env` file |

### finnews-db

| Property | Value |
|----------|-------|
| Image | `postgres:16-alpine` |
| Exposed port | 5432 |
| Persistent volume | `postgres_data:/var/lib/postgresql/data` |
| Restart policy | `unless-stopped` |
| Env vars | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` |

## Environment-Based Configuration

All configuration via environment variables. Never hardcoded.

| Variable | Dev Default | Production |
|----------|-------------|-----------|
| `APP_ENV` | `development` | `production` |
| `LOG_LEVEL` | `INFO` | `WARNING` |
| `POSTGRES_HOST` | `db` (Docker) / `localhost` (local) | Internal hostname |
| `POSTGRES_PASSWORD` | `postgres` | Strong secret |
| `BACKEND_PORT` | `8000` | `8000` |

## What We Don't Use (and Why)

| Technology | Why Not |
|-----------|---------|
| Kubernetes | Single-host deployment, no need for orchestration complexity |
| Nginx reverse proxy | Not needed until multiple services or TLS termination required |
| Cloud-managed DB | Docker PostgreSQL is sufficient for this phase |
| CI/CD pipeline | Manual docker compose deployments for now |
| Secrets manager | `.env` file is sufficient at this scale |
| Multi-stage build | Build step is fast with uv; not worth the complexity |

## Future Considerations (not now)

- Add nginx as reverse proxy when TLS is needed
- Add Streamlit container alongside backend
- Consider managed PostgreSQL if data grows beyond single-volume capacity
- Add GitHub Actions for lint + test on PR
