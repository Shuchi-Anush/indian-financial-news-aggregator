# System Architecture

## Core Design Principles
This backend is designed as an asynchronous, IO-bound data aggregation platform.
The architecture avoids premature microservice extraction by operating as a modular monolith, separating API responsibilities from background ingestion through isolated concurrency loops.

## Trade-offs
- **Monolith over Microservices**: Reduces network overhead and simplifies deployments, but forces API memory limits and Ingestion memory limits to share the same container scope.
- **Embedded Scheduler over Celery**: Eliminates Redis/RabbitMQ infrastructure dependency, but binds scheduled execution to the lifespan of the API web server.
- **Regex Enrichment over ML**: Guarantees ultra-fast throughput and zero external API dependencies, but sacrifices semantic accuracy and context-awareness.

## 1. Ingestion Pipeline & Async Flow
The core lifecycle of data acquisition:
1. **Trigger**: `APScheduler` initiates the `run_ingestion_cycle` job.
2. **Collect**: `RSSCollector` concurrently sweeps active `FeedSource` URLs via `httpx`.
3. **Parse & Normalize**: Raw XML is parsed. `url` canonicalization drops tracking parameters.
4. **Enrich**: `DeterministicEnricher` scans text for keywords, overriding coarse sentiment/category.
5. **Deduplicate & Persist**: Using SHA-256 `content_hash` over the payload, PostgreSQL guarantees uniqueness via `ON CONFLICT (url) DO NOTHING`.

## 2. Observability & Resilience Systems
The architecture expects upstream failure as a baseline state.
- **Circuit Breaker**: `RSSCollector` maintains internal state for failed domains. `HTTP 500/429` increment error counts. After a threshold, domains transition to `OPEN` and are temporarily skipped, preventing pipeline starvation.
- **Pipeline Tracking**: Every ingestion run receives a UUID, logging start time, stop time, ingested counts, and serialized arrays of failed sources.
- **Prometheus Metrics**: Crucial execution stats (e.g., `pipeline_runs_total`, `articles_ingested_total`) are mapped to the `/metrics` endpoint.

## 3. Database Strategy
- **Keyset Pagination**: Traditional `OFFSET` degrades at high scale. The API uses `published_at, id` composite indices to serve `cursor`-based pagination, executing in $O(1)$ time regardless of depth.
- **Search Strategy**: `tsvector` generated columns allow native GIN-indexed full-text searching across titles and body contents without needing external indexing clusters.

## 4. Analytics & Materialized Views
To answer aggregate questions ("How many positive articles mentioned banking today?"), standard aggregate `GROUP BY` queries become too expensive over millions of rows.
- **Solution**: We use PostgreSQL `MATERIALIZED VIEW`.
- **Refresh**: Triggered by the orchestration pipeline post-ingestion.

## Bottlenecks & Scalability Limits
- **Postgres Write Locks**: Massive concurrent inserts during bulk ingestion might cause contention on the `url` unique index.
- **MV Refresh Overhead**: Synchronous materialized view refreshes block DB resources. At higher scale, this must move to `CONCURRENTLY`.
- **Memory Boundaries**: The FastAPI worker memory scales linearly with the size of the payloads processed in `gather()` loops.

## Future Evolution Path
When the single-node DB boundary is crossed, the following must occur:
1. Table Partitioning on `articles`.
2. Detachment of `APScheduler` into a discrete container/worker layer.
3. Decoupling Search to OpenSearch.
