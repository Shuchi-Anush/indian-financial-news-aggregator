# Walkthrough: Phase 1 — Backend Core Runtime Foundation

## Files Implemented

| File | Lines | Responsibility |
|------|-------|---------------|
| [core/__init__.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/__init__.py) | 1 | Package marker |
| [core/config.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/config.py) | 66 | Typed settings via pydantic-settings, cached loader |
| [core/logging.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/logging.py) | 72 | Structlog setup — dev console / prod JSON modes |
| [core/exceptions.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/exceptions.py) | 121 | Domain exception hierarchy + FastAPI error handlers |
| [core/middleware.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/middleware.py) | 119 | Request ID, request logging, CORS |
| [core/startup.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/startup.py) | 47 | Lifespan context manager (startup/shutdown) |
| [db/base.py](file:///d:/indian-financial-news-aggregator/backend/src/app/db/base.py) | 50 | Declarative base + TimestampMixin |
| [db/session.py](file:///d:/indian-financial-news-aggregator/backend/src/app/db/session.py) | 78 | Async engine lifecycle + session DI |
| [main.py](file:///d:/indian-financial-news-aggregator/backend/src/app/main.py) | 39 | Composition root — wires everything |

**Also modified:** [Dockerfile](file:///d:/indian-financial-news-aggregator/backend/Dockerfile) — changed CMD to use `--app-dir src` for correct import resolution.

---

## Key Design Decisions

### Import Path: `app.*` with `--app-dir src`
The project uses a `src/` layout. Instead of `from src.app.core.config import ...`, all imports use `from app.core.config import ...` — the standard convention for src-layout Python projects. The Dockerfile and uvicorn invocation use `--app-dir src` to set the correct root.

### Logging Before Everything
`setup_logging()` is called at module-level in `main.py` before any other imports. This ensures structlog is configured before the first log event (including startup logs from the lifespan handler).

### Module-Level DB State
`db/session.py` uses module-level `_engine` and `_session_factory` variables initialized once during startup via `init_engine()`. This avoids DI frameworks or global state managers while remaining testable (can call `init_engine()` with different configs in tests).

### Exception Hierarchy
```
AppError (500, internal_error)
├── NotFoundError (404, not_found)
├── CollectorError (502, collector_error)
├── NormalizationError (422, normalization_error)
├── DuplicateArticleError (409, duplicate_article)
└── ExportError (500, export_error)
```
Each exception carries `status_code`, `error_code`, `message`, and optional `details`. The FastAPI handler converts them into consistent `{error, message, details?}` JSON.

### Middleware Order (LIFO)
Registered in this order (LIFO means first-registered = outermost):
1. `RequestIdMiddleware` — generates UUID, binds to structlog contextvars
2. `RequestLoggingMiddleware` — logs method/path/status/duration (includes request_id from contextvars)
3. `CORSMiddleware` — permissive in dev, locked down in prod

---

## Verification Results

### Import Check (no circular deps)
```
[OK] logging
[OK] exceptions
[OK] middleware
[OK] startup
[OK] db/base
[OK] db/session
[OK] ALL IMPORTS PASSED — no circular dependencies
```

### Server Startup
```
application_startup            app_env=development backend_port=8000 postgres_host=localhost
database_engine_initialized
Application startup complete.
Uvicorn running on http://127.0.0.1:8000
```

### Request Tracing
```
request_completed  method=GET path=/health       status=200 duration_ms=12.06 request_id=1b28d4bb-...
request_completed  method=GET path=/openapi.json  status=200 duration_ms=21.05 request_id=2e068e44-...
request_completed  method=GET path=/nonexistent   status=404 duration_ms=0.2   request_id=cfaa9b40-...
```

### Health Check Response
```json
{"status": "ok"}
```

---

## Run Commands

```bash
# From backend/ directory:

# Install dependencies
uv sync

# Start server (local dev)
uv run uvicorn app.main:app --app-dir src --reload --host 127.0.0.1 --port 8000

# Verify
curl http://127.0.0.1:8000/health
# → {"status":"ok"}

# Docker (full stack)
docker compose up --build
```

---

## Extension Points for Next Phase

| Next Step | Where |
|-----------|-------|
| Add ORM models (Article, FeedSource) | `models/article.py`, `models/feed_source.py` |
| Add Pydantic schemas | `schemas/article.py`, `schemas/feed.py` |
| Add `create_all()` to lifespan | `core/startup.py` (after `init_engine()`) |
| Add API routes | `api/routes/` → mount in `main.py` |
| Add services | `services/` → use `get_db()` via DI |
