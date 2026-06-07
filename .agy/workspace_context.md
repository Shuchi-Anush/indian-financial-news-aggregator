# Workspace Context

## Project

**Indian Financial News Aggregator** — a modular FastAPI backend that collects Indian financial news from RSS feeds/APIs, normalizes articles, deduplicates content, stores structured data in PostgreSQL, and exports via REST API and CSV/Excel.

## Current Phase

**Phase 1: Backend Infrastructure & Ingestion Pipeline**

Building the core `collect → normalize → deduplicate → persist → export` pipeline. Frontend is out of scope for this phase.

## Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.115+ |
| Validation | Pydantic | v2.8+ |
| ORM | SQLAlchemy | 2.0+ (async) |
| Database | PostgreSQL | 16 (Docker) |
| HTTP Client | httpx | 0.27+ |
| RSS Parser | feedparser | 6.0+ |
| Fuzzy Match | rapidfuzz | 3.9+ |
| Logging | structlog | 24.4+ |
| Export | pandas + openpyxl | |
| Package Mgr | uv | latest |
| Container | Docker Compose | |

## Repository State

- Directory skeleton: ✅ complete
- Dependencies: ✅ declared in pyproject.toml
- Docker Compose: ✅ PostgreSQL + backend
- Module implementations: ❌ all empty (except main.py health check)
- Tests: ❌ not started
- Documentation: ✅ governance layer complete

## Key Files

- Entry point: `backend/src/app/main.py`
- Config: `backend/src/app/core/config.py`
- Dependencies: `backend/pyproject.toml`
- Environment: `.env` / `.env.example`
- Docker: `docker-compose.yml` + `backend/Dockerfile`

## Environment

- Dev machine: Windows
- Runtime: Docker (linux containers)
- DB host in Docker: `db` (service name)
- DB host for local dev: `localhost`
- Backend port: 8000
- PostgreSQL port: 5432
