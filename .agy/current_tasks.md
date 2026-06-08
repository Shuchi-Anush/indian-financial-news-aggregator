# Current Tasks

This file tracks the immediate next actions. Updated as work progresses.

## Next Up

- [ ] Implement `models/article.py` — Article ORM model
- [ ] Implement `models/feed_source.py` — FeedSource ORM model
- [ ] Implement `schemas/article.py` — ArticleCreate, ArticleRead, ArticleFilter
- [ ] Implement `schemas/feed.py` — FeedSourceCreate, FeedSourceRead
- [ ] Add `create_all()` to startup lifespan (after models exist)

## Blocked

_Nothing currently blocked._

## Recently Completed

- [x] Repository skeleton created
- [x] Dependencies declared in pyproject.toml
- [x] Docker Compose setup (PostgreSQL + backend)
- [x] Documentation governance layer completed
- [x] AI context files (.claude/) populated
- [x] Operational context (.agy/) populated
- [x] Architecture decisions documented (ADR-001 through ADR-003)
- [x] `core/config.py` — Typed settings via pydantic-settings
- [x] `core/logging.py` — Structlog setup (dev console / prod JSON)
- [x] `core/exceptions.py` — Exception hierarchy + FastAPI handlers
- [x] `core/middleware.py` — Request ID, logging, CORS
- [x] `core/startup.py` — Lifespan context manager
- [x] `db/base.py` — Declarative base + TimestampMixin
- [x] `db/session.py` — Async engine lifecycle + session DI
- [x] `main.py` — Composition root wiring
- [x] Dockerfile updated for `--app-dir src` pattern
- [x] Server startup verified — health check, request tracing, structured logging
