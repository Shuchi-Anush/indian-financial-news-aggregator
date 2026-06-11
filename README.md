# Indian Financial News Aggregator

An operationally mature, high-throughput financial news aggregation platform. This backend system systematically ingests, normalizes, deduplicates, enriches, and serves Indian financial market news at scale.

## Platform Overview
The system is built as a production-grade FastAPI service backed by asynchronous PostgreSQL, utilizing an embedded APScheduler for ingestion orchestration. It targets the continuous collection of RSS feeds from major Indian financial outlets (Moneycontrol, Economic Times, LiveMint, CNBC TV18), converting raw XML into normalized, deduplicated, and semantically enriched entities.

## Major Capabilities
- **Continuous Ingestion Engine**: Configurable, asynchronous fetching of multiple RSS sources via embedded scheduling.
- **Resilient Orchestration**: Circuit breakers, exponential backoff, and localized exception handling prevent poisoned feeds from crashing the system.
- **Deterministic Enrichment**: Fast, regex-and-dictionary-based entity, sector, and sentiment extraction avoiding heavy ML bottlenecks.
- **Keyset Pagination**: Zero-offset keyset traversal ensuring constant-time latency (`O(1)`) even at millions of rows.
- **Full-Text Search**: Native PostgreSQL `tsvector` / GIN indexing for fast, complex queries.
- **Observability**: Built-in Prometheus `/metrics` exposing circuit-breaker states, pipeline durations, and failure rates.
- **Bulk Export Subsystem**: Streaming CSV exports capable of handling large dataset dumps without memory exhaustion.
- **Analytics Materialization**: Background-refreshed materialized views for rapid trending and sentiment aggregations.

## Tech Stack
- **API Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 (Relational, JSONB, tsvector)
- **ORM / Querying**: SQLAlchemy 2.0 (Strict Asyncio Native)
- **Migrations**: Alembic
- **Task Orchestration**: APScheduler (Embedded AsyncIOScheduler)
- **HTTP Client**: `httpx` (Fully Async)
- **XML Parsing**: `feedparser`
- **Validation / Types**: Pydantic v2
- **Metrics**: `prometheus-client`
- **Package Management**: `uv`

## System Architecture Summary
The system adheres strictly to the Repository/Service/Router pattern:
1. **API Routers**: `app.api.routes` — Handle HTTP transport, Pydantic validation, and response mapping.
2. **Services**: `app.services` — Coordinate domain logic, orchestration, and enrichment pipelines.
3. **Repositories**: `app.db.repository` — Map pure Python domains to SQLAlchemy execution boundaries.
4. **Database**: Managed strictly via async SQLAlchemy core/ORM hybrid. `ON CONFLICT DO NOTHING` logic ensures strict uniqueness on `url` and `content_hash`.

## Quickstart

### Docker
```bash
# Bring up the stack (PostgreSQL + FastAPI backend)
docker compose up -d

# Check logs
docker compose logs -f backend
```

### Local Development
Please refer to [LOCAL_DEVELOPMENT.md](docs/development/LOCAL_DEVELOPMENT.md) for extensive rules on local setup (`uv sync`, DB initialization, validation loops).

## Operational Knowledge
- **Deployment**: [DEPLOYMENT.md](docs/operations/DEPLOYMENT.md)
- **Operations & Runbooks**: [OPERATIONS.md](docs/operations/OPERATIONS.md)
- **Observability & Monitoring**: [MONITORING.md](docs/operations/MONITORING.md)
- **Security**: [SECURITY.md](docs/operations/SECURITY.md)

## Production Readiness Statement
This backend has undergone brutal validation, encompassing DB-level deadlock/concurrent locking simulations, chaos injection via malformed ingestion feeds, and payload brutalization. All components are strictly async, type-checked (mypy strict), logically bounded against memory bloat, and instrumented for observability. It is inherently production-ready.

## API Highlights
All routes are prefixed by `/articles`, `/analytics`, or `/admin`. See [API_REFERENCE.md](docs/api/API_REFERENCE.md) for exhaustive contracts.
- `GET /articles?limit=50&cursor={base64}`: Constant-time feed delivery.
- `GET /articles/export/csv`: Streaming bulk export.
- `GET /analytics/trending`: Summarized sector/entity momentum via materialized views.
- `GET /metrics`: Prometheus metric endpoint.
