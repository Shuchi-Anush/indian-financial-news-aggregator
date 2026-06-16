# Backend Engineering Handbook

This document serves as the internal technical reference for the Indian Financial News Aggregator backend. It covers the architectural design decisions, execution boundaries, operational characteristics, and engineering tradeoffs of the core data platform.

## 1. Backend Overview

The backend is an asynchronous Python service built upon FastAPI and SQLAlchemy 2.x. It diverges significantly from standard CRUD REST applications; its primary operational posture is that of a heavy-duty data ingestion and aggregation engine. Its core responsibilities involve orchestrating volatile external network I/O, executing deterministic deduplication logic, and enforcing strict transactional persistence boundaries.

## 2. Runtime Architecture

![Backend Runtime](../docs/assets/backend_runtime.png)

The application initializes its global state through an asynchronous lifespan context. Upon Uvicorn worker boot:
1. The PostgreSQL engine connection pool is instantiated.
2. Alembic schema migrations are verified.
3. The `APScheduler` is mounted directly to the running `asyncio` event loop.

This runtime topology ensures that the FastAPI workers simultaneously handle inbound API requests and outbound background ingestion jobs within the same isolated process, eliminating the immediate need for external queuing infrastructure.

## 3. Request Lifecycle

The API enforces strict topological layering to decouple HTTP transport from business domain logic:

1. **Middleware**: Injects UUID trace IDs, resolves CORS, and intercepts unhandled exceptions to prevent worker crashes.
2. **Router (`app.api`)**: Performs Pydantic validation and deserializes HTTP payloads. No business logic or database dependencies exist at this layer.
3. **Service (`app.services`)**: Coordinates repositories, invokes external collectors, and executes domain transformations.
4. **Repository (`app.db.repository`)**: Translates domain intents into safe, asynchronous SQLAlchemy execution statements.
5. **Database**: Executes queries within bounded `AsyncSession` transactions.

## 4. Scheduler Lifecycle

The embedded `AsyncIOScheduler` triggers the `run_ingestion_cycle` coroutine natively within the primary event loop. The scheduler is configured defensively:
- Execution is wrapped in global exception handlers to ensure poisoned XML payloads do not crash the Uvicorn worker.
- Graceful shutdown hooks drain pending scheduler tasks before the application is permitted to terminate.

## 5. Ingestion Lifecycle

![Orchestration Pipeline](../docs/assets/orchestration_pipeline.png)

The ingestion flow models a strict pipeline of transformations:

1. **Target Discovery**: Active feeds are hydrated from the `feed_sources` registry.
2. **Concurrent Fetching**: The `RSSCollector` issues non-blocking HTTP requests via `httpx`.
3. **Parsing & Normalization**: Raw payloads are mapped into a standardized `RawArticle` intermediate model. HTML entities are stripped, and ambiguous time zones are forced to UTC.
4. **Enrichment**: Named entities and sectors are extracted deterministically based on regex and dictionary heuristics.
5. **Persistence Handoff**: The parsed payload is handed to the service orchestration layer to initiate database transactions.

## 6. Persistence Flow

![Persistence Flow](../docs/assets/persistence_flow.png)

To guarantee idempotency at scale, the system avoids costly "read-before-write" existence checks. Instead, deduplication constraints are pushed directly to the storage engine. 

Articles are batched into an `AsyncSession`, and an `INSERT ... ON CONFLICT DO NOTHING` statement is executed. This guarantees strict uniqueness even when multiple workers overlap their scraping windows.

## 7. Database Architecture

![Database Schema](../docs/assets/database_schema.png)

The schema design prioritizes high-throughput inserts and rapid read access:
- **`feed_sources`**: Tracks the URLs, metadata, and circuit breaker states of RSS providers.
- **`articles`**: The canonical persistence layer. The `content_hash` field enforces deterministic uniqueness. The `search_vector` field enables native GIN-indexed full-text search.
- **`pipeline_runs`**: Operational telemetry tracking the duration and duplicate counts of specific ingestion cycles.

## 8. Repository Pattern Explanation

We utilize the Repository pattern to construct an impermeable boundary around the SQLAlchemy ORM. 
- Services never import SQLAlchemy models or construct SQL queries. 
- The `ArticleRepository` exposes high-level domain operations (`get_paginated`, `upsert_batch`).
This boundary ensures that complex query optimizations—such as zero-offset keyset pagination—can be isolated and refactored without corrupting business logic.

## 9. Service Layer Explanation

The Service layer acts as the primary transaction coordinator. The `PipelineOrchestrationService` manages the boundaries between fetching, parsing, and persistence. It controls the `async with session.begin():` block, ensuring that if a batch of articles fails to insert, the corresponding pipeline telemetry reflects the failure atomically.

## 10. Deduplication Strategy

The system achieves deduplication through cryptographic hashing. When a payload is parsed, a deterministic SHA-256 hash (`content_hash`) is computed from the article's URL and body.

This hash serves as a secondary unique identifier. During persistence, the `UPSERT` logic relies on this hash to discard records that have already been ingested, allowing the pipeline to safely process overlapping RSS windows repeatedly.

## 11. Search Architecture

Search functionality avoids the operational overhead of external search engines like Elasticsearch. Instead, the `articles` table maintains a `tsvector` column (`search_vector`). API requests use `to_tsquery` to perform complex, highly-performant full-text searches across millions of rows directly within PostgreSQL.

## 12. Analytics Materialization

Running aggregate `COUNT` and `GROUP BY` operations across the article table to calculate trending sectors is computationally prohibitive. 
To resolve this, the system leverages PostgreSQL **Materialized Views** (`hourly_trends_mv`). These views are refreshed via `REFRESH MATERIALIZED VIEW CONCURRENTLY` in background hooks, allowing the API to return complex analytics data with flat $O(1)$ latency.

## 13. Export Subsystem

Financial researchers require vast datasets. Attempting to serialize 100,000 ORM objects into memory to generate a CSV would trigger Out-Of-Memory (OOM) killer terminations. 
The `GET /articles/export/csv` route implements FastAPI's `StreamingResponse` alongside server-side database cursors. Data is fetched and yielded in small chunks, maintaining a flat memory footprint regardless of the export size.

## 14. Performance Characteristics

- **Ingestion**: Strictly network-bound. Utilizing `httpx` allows hundreds of feeds to be collected concurrently.
- **Serving**: Disk I/O bound. The implementation of keyset pagination prevents the deep-offset degradation typical in `LIMIT/OFFSET` designs.
- **Memory**: Bounded safely. Streaming responses and lazy-loaded async queries protect the workers from payload bloat.

## 15. Scaling Considerations

The platform currently operates as a scalable monolith. To scale horizontally to massive ingestion workloads:
1. **API Tier**: Completely stateless; can be trivially replicated behind a load balancer.
2. **Ingestion Tier**: The embedded `APScheduler` poses a risk of redundant fetching if the container is scaled. The architectural roadmap requires migrating the scheduler state to a Redis/Celery queue to safely distribute fetch jobs across worker nodes.

## 16. Failure Handling

- **Poisoned Feeds**: XML parsing is bounded by aggressive `try/except` blocks. Feed-specific failures log warnings and increment error telemetry without crashing the orchestration loop.
- **Database Resilience**: SQLAlchemy is configured with `pool_pre_ping=True` to seamlessly recycle broken connections.
- **Circuit Breakers**: Repeated timeouts on specific RSS sources trip internal circuit breakers, backing off requests to prevent resource starvation.

## 17. Observability

Operational visibility is built-in. The `/metrics` endpoint exposes Prometheus data:
- `ingestion_pipeline_duration_seconds` (Histogram)
- `articles_ingested_total` (Counter)
- `circuit_breaker_failures_total` (Counter)

Structured logging (`structlog`) is utilized universally, ensuring that every operation is logged as a parseable, JSON-serialized event annotated with a request UUID.

## 18. Local Development

```bash
cd backend
uv sync
alembic upgrade head
uv run uvicorn app.main:app --reload
```

*Note: Ensure `POSTGRES_USER` and `POSTGRES_PASSWORD` are valid in your `.env`. Do not run multiple local terminal windows hosting the embedded scheduler to avoid local ingestion race conditions.*

## 19. Production Deployment

The backend is shipped as a multi-stage, distroless-like Docker container. The included `entrypoint.sh` strictly enforces state transition ordering:
1. Waits for PostgreSQL socket readiness.
2. Executes `alembic upgrade head`.
3. Boots the Uvicorn ASGI server.

In high-throughput environments, database connections should be routed through a connection pooler (e.g., `PgBouncer`), as the internal `AsyncEngine` pool size is tuned conservatively.

## 20. Engineering Tradeoffs

**Embedded Scheduler vs Distributed Queue**
- *Decision*: We embedded `APScheduler` instead of deploying Celery + Redis.
- *Rationale*: Greatly simplified operational overhead during the v1 rollout.
- *Tradeoff*: We cannot currently scale the ingestion worker horizontally without causing duplicate fetch execution.

**PostgreSQL Native Search vs Elasticsearch**
- *Decision*: We utilized `tsvector` and GIN indexing natively in PostgreSQL.
- *Rationale*: Drastically reduced infrastructure complexity; avoided the "dual-write" consistency problem.
- *Tradeoff*: Advanced linguistic features (e.g., fuzzy matching, deep synonym expansion) are less capable than dedicated search engines.

**Materialized Views vs Redis Caching**
- *Decision*: We compute analytics via PostgreSQL Materialized Views instead of a Redis cache.
- *Rationale*: Allowed us to lean entirely on SQL for aggregation logic without deploying a secondary data store.
- *Tradeoff*: Data freshness is tied to the manual refresh cycle of the view, leading to potential minor staleness compared to event-driven cache invalidation.
