# System Design Document

This document provides a rigorous architectural analysis of the Indian Financial News Aggregator. Designed as a system-design case study, it details the explicit engineering tradeoffs, data lifecycle boundaries, scalability limitations, and reliability mechanisms governing the platform in production environments.

---

## Architectural Goals

1. **Absolute Idempotency**: The core ingestion engine must be able to repeatedly process overlapping, redundant data feeds without corrupting the persistence layer or generating duplicate state.
2. **Asynchronous Isolation**: The ingestion of volatile external data must never block the event loop responsible for serving HTTP API requests.
3. **Bounded Memory Execution**: Bulk operations—such as CSV extraction and full-text search indexing—must operate within strictly flat memory footprints to prevent container Out-Of-Memory (OOM) terminations.
4. **Zero-Touch Bootstrap**: The system must autonomously transition from a cold start to a fully operational ingestion and serving state without manual database migrations or operational scripting.

## Non-Goals

1. **Real-Time Streaming**: Sub-second websocket syndication of news is explicitly out of scope for the current architecture; 15-minute eventual consistency is the accepted SLA.
2. **Deep Semantic Search**: Fuzzy matching, NLP-driven semantic search, and typo-tolerance are excluded in favor of exact-prefix matching to avoid deploying Elasticsearch.
3. **Microservices Overhead**: The system will not adopt Kubernetes, Kafka, or gRPC until the monolithic architecture provably exhausts its vertical scaling limits.

## Constraints

- **Execution Topology**: The scheduler and the API operate within the same Python memory space and event loop.
- **Compute Overhead**: Machine learning pipelines (NER, Sentiment Analysis) are restricted, as heavy CPU-bound synchronous tasks will starve the asyncio event loop and degrade API latency.

## Architecture Drivers

The architecture is driven by the hostility of the external internet. Financial RSS feeds suffer from frequent timeouts, undocumented schema changes, malformed XML, and unpredictable Cloudflare bot-challenges. The architecture must treat external data as inherently poisonous and wrap it in rigid, isolated boundaries.

---

## System Architecture

![System Architecture](../docs/assets/system_architecture.png)

The system deploys as a containerized monolith utilizing Docker Compose. 

### Edge Boundary (Nginx)
Nginx acts as the reverse proxy and first line of defense. It routes traffic securely, terminates TLS (in production), enforces rate limiting, and maps `/api` paths to the FastAPI backend while serving the operational dashboard on the root path.

### Backend Execution (FastAPI)
The FastAPI container houses the application logic. It operates in two simultaneous capacities:
1. **API Worker**: Uvicorn processes listening for incoming TCP connections.
2. **Background Orchestrator**: The APScheduler thread initiating outbound network requests.

### Persistence Engine (PostgreSQL)
PostgreSQL is the singular source of truth. It manages relational data, executes full-text search indexing via GIN, enforces uniqueness constraints via hash algorithms, and pre-computes complex analytics via materialized views.

---

## End-to-End Data Lifecycle

![Pipeline Flow](../docs/assets/pipeline_flow.png)

The journey of an article follows strict immutability principles:

1. **Collection**: Raw XML payloads are fetched from external endpoints into memory.
2. **Normalization**: The XML tree is parsed. HTML entities in descriptions are sanitized to prevent XSS and normalize search text. Timezones are localized and forced to UTC. The data is mapped to a strictly-typed Pydantic DTO (`RawArticle`).
3. **Deduplication Hashing**: A deterministic SHA-256 hash is computed based on the canonical URL and core content.
4. **Enrichment**: Configurable heuristics scan the text to attach sector labels (e.g., "Technology") and flag named entities.
5. **Persistence**: The asynchronous repository opens a transaction and upserts the payload to PostgreSQL, relying on the hash to reject duplicates.
6. **Analytics Hook**: Post-commit hooks trigger the database to refresh materialized views.
7. **API Serving**: The normalized payload is serialized to JSON and served to consumers via keyset paginated HTTP routes.

---

## RSS Source Strategy

The platform does not rely on a monolithic stream. It maintains a dictionary of targeted sources.

- **Source Selection**: Curated list of high-signal Indian publishers (Moneycontrol, Economic Times, LiveMint, Business Standard).
- **Validation**: Sources are polled for XML integrity. Feeds lacking functional `guid` or `pubDate` fields are rejected at the source configuration level.
- **Reliability Tracking**: The database tracks consecutive failures per source, providing telemetry on publisher uptime and API volatility.

---

## Ingestion Design

Ingestion is fundamentally asynchronous and network-bound. Utilizing `httpx.AsyncClient`, the system fires concurrent requests to all active RSS sources. 

This concurrency is heavily bounded. A semaphore restricts simultaneous outbound connections to prevent IP bans or file-descriptor exhaustion. The `feedparser` library executes the actual XML parsing; because `feedparser` is a blocking, CPU-bound library, it is executed via `asyncio.to_thread()` to prevent starving the FastAPI event loop during massive payload deserialization.

---

## Scheduler Design

![Orchestration Pipeline](../docs/assets/orchestration_pipeline.png)

The `PipelineOrchestrationService` manages the scheduler. The system embeds `APScheduler` inside the Uvicorn worker.

It operates on a strictly interval-based cron tick. Concurrency controls (`max_instances=1`) guarantee that a delayed ingestion cycle will not overlap with the subsequent scheduled cycle. The orchestrator acts as the ultimate transaction boundary—it dictates when a database session begins, commits, or rolls back based on the holistic success of the feed collection.

---

## Deduplication Design

Deduplication logic is offloaded entirely to the storage engine. 

Attempting application-level deduplication (e.g., querying the database with `SELECT id FROM articles WHERE url IN (...)`) requires holding thousands of URLs in memory, executing expensive index scans, and manually filtering payloads before insert. It is highly susceptible to race conditions if two worker threads process the same feed simultaneously.

Instead, the pipeline generates a `content_hash`. The PostgreSQL schema enforces a `UNIQUE` constraint on this column. 
The system executes a bulk `INSERT INTO ... ON CONFLICT (content_hash) DO NOTHING`. 
The PostgreSQL C engine resolves hash index collisions in microseconds, guaranteeing 100% idempotency with zero application-side race conditions.

---

## Persistence Design

![Persistence Flow](../docs/assets/persistence_flow.png)

The persistence layer strictly adheres to the Unit of Work and Repository patterns.

- **`articles`**: The canonical storage table. Highly indexed for time-series and full-text search.
- **`feed_sources`**: The configuration table driving the ingestion loop.
- **`pipeline_runs`**: The operational telemetry table. Records the start time, end time, duration, and article yield of every scheduler execution. 

If a batch of articles fails to insert (due to a database disconnect), the `pipeline_runs` entry is rolled back alongside the articles, ensuring the telemetry remains perfectly synchronized with actual disk state.

---

## Database Design

![Database Schema](../docs/assets/database_schema.png)

The schema rationale prioritizes high-throughput inserts and immutable history. Soft deletes are avoided in favor of strict retention policies. The `search_vector` column is explicitly decoupled from the text columns to allow customized trigger-based text weighting in the future.

---

## Search Design

Search functionality avoids the operational overhead of deploying Elasticsearch. The `articles` table maintains a `tsvector` column (`search_vector`) updated via SQLAlchemy triggers upon insert. 

When a user queries the API, the backend constructs a `to_tsquery` execution plan. PostgreSQL utilizes a Generalized Inverted Index (GIN) to locate records. To paginate through massive result sets without performance degradation, the API requires zero-offset keyset pagination (cursor-based), explicitly rejecting `LIMIT/OFFSET` anti-patterns.

---

## Analytics Design

Running aggregate `COUNT` and `GROUP BY` operations across the article table to calculate trending sectors is computationally prohibitive. 

The system leverages PostgreSQL **Materialized Views** (e.g., `hourly_trends_mv`). These views pre-aggregate complex metrics into physical tables. When the API requests trending data, it queries the view directly ($O(1)$ latency). The orchestration service triggers a `REFRESH MATERIALIZED VIEW CONCURRENTLY` in the background, ensuring analytics remain fresh without blocking concurrent read traffic.

---

## Export Design

Financial researchers require bulk data access. The `GET /api/articles/export/csv` route implements an async `StreamingResponse`. 

Rather than loading the dataset into RAM, the backend opens a server-side PostgreSQL cursor. It fetches data in chunks of 1,000, formats them as CSV rows, and yields them over the HTTP socket. This bounded stream prevents memory exhaustion (OOM crashes), allowing a 1GB API container to safely generate and transmit a 50GB CSV file.

---

## Failure Scenarios

The system's resilience is defined by its response to failure.

### 1. Malformed RSS XML
- **Detection**: `feedparser` throws an exception or returns a fundamentally broken dictionary missing mandatory fields (URL, Title).
- **Impact**: Isolated to the specific article.
- **Mitigation**: Quality gates drop the invalid payload. A `dropped_malformed_article` metric is incremented. The pipeline continues.
- **Residual Risk**: A publisher completely changing their schema will result in 100% dropped articles for that source until the parsing heuristics are updated.

### 2. HTTP 403 (Anti-Bot)
- **Detection**: `httpx` returns a 403 status code.
- **Impact**: The specific feed fails collection.
- **Mitigation**: The internal circuit breaker logs the failure. Repeated failures trip the breaker, applying exponential backoff to the source.
- **Residual Risk**: Publisher IP-blocks require manual proxy routing or User-Agent rotation.

### 3. Feed Timeout
- **Detection**: `httpx` exceeds the strict 10-second read timeout.
- **Impact**: Collection hangs temporarily.
- **Mitigation**: Timeouts are aggressively enforced. The feed fails, the breaker increments, and the orchestrator moves on.
- **Residual Risk**: None. Strict timeouts prevent the ingestion thread from hanging indefinitely.

### 4. Duplicate Articles
- **Detection**: The database hash index detects a collision on `content_hash`.
- **Impact**: None.
- **Mitigation**: Handled natively via `ON CONFLICT DO NOTHING`.
- **Residual Risk**: If a publisher subtly modifies an article (changing the hash), the system ingests it as a new distinct article.

### 5. Scheduler Crash
- **Detection**: Prometheus telemetry (`time_since_last_successful_run`) exceeds thresholds.
- **Impact**: New articles cease flowing into the database.
- **Mitigation**: Kubernetes/Docker restarts the unhealthy container based on `/health` endpoint staleness.
- **Residual Risk**: Data freshness gap during the downtime window.

### 6. Database Outage
- **Detection**: SQLAlchemy raises `ConnectionRefusedError`.
- **Impact**: API requests fail (500). Ingestion cycles fail.
- **Mitigation**: `pool_pre_ping` attempts to reconnect. The API and scheduler will crash repeatedly until the database recovers, ensuring no data is acknowledged as saved when it isn't.
- **Residual Risk**: Hard dependency on PostgreSQL uptime.

### 7. Restart During Ingestion
- **Detection**: SIGTERM received mid-batch insert.
- **Impact**: The current transaction is severed.
- **Mitigation**: Database rolls back the incomplete batch. Upon restart, the scheduler re-fetches the feed, safely idempotently inserting the data.
- **Residual Risk**: None. Transactions guarantee atomic safety.

### 8. Materialized View Failure
- **Detection**: The `REFRESH` SQL command fails (e.g., due to deadlock).
- **Impact**: Analytics dashboards display stale data.
- **Mitigation**: The API continues serving the previously materialized state. The next ingestion cycle will re-attempt the refresh.
- **Residual Risk**: Temporary metric drift.

---

## Scalability Analysis

### Current Limits
- **Ingestion Throughput**: Network bound. Can realistically process ~500 RSS feeds every 15 minutes on a single CPU core.
- **Storage Limits**: Bounded only by PostgreSQL disk capacity.
- **Serving Limits**: Bounded by ASGI concurrency. Easily handles thousands of requests per second due to keyset pagination.

### Future Limits & Bottlenecks
- **The Embedded Scheduler**: Because `APScheduler` is embedded, deploying a second FastAPI container to scale API traffic will result in the second container *also* attempting to fetch RSS feeds. While advisory locks mitigate this, the architecture prevents explicitly scaling the ingestion tier out to multiple nodes.

---

## Alternative Architectures Considered

### ADR-001: PostgreSQL Search vs Elasticsearch
- **Context**: The platform requires fast full-text search across millions of news articles.
- **Decision**: Utilize PostgreSQL `tsvector` and GIN indexing natively.
- **Rationale**: Adding Elasticsearch requires massive RAM overhead, JVM tuning, and a complex CDC (Change Data Capture) pipeline to keep the search index in sync with the relational database.
- **Tradeoffs**: PostgreSQL search lacks deep linguistic capabilities, fuzzy matching, and typo-tolerance.
- **Consequences**: Substantially reduced infrastructure footprint and operational overhead, at the cost of less "intelligent" search query parsing.

### ADR-002: Embedded APScheduler vs Celery
- **Context**: The platform requires recurring background tasks to execute ingestion.
- **Decision**: Embed `APScheduler` directly inside the FastAPI ASGI event loop.
- **Rationale**: Celery requires a message broker (Redis/RabbitMQ) and separate worker containers. For a v1 deployment focused on validation, this added unacceptable operational complexity.
- **Tradeoffs**: We lose horizontal scalability of the ingestion tier and the ability to easily distribute retries across nodes.
- **Consequences**: Ingestion is locked to a single node.

### ADR-003: Monolith vs Microservices
- **Context**: The platform executes distinct domains: Fetching, Serving, Analytics.
- **Decision**: Deploy as a single monolithic Python repository and container.
- **Rationale**: Microservices introduce extreme complexity (network partitions, distributed tracing, complex CI/CD). The team size and project scope did not justify this boundary.
- **Tradeoffs**: A massive CPU spike during XML parsing could theoretically degrade API response times.
- **Consequences**: Faster development velocity and trivial deployment topology.

### ADR-004: Materialized Views vs External Analytics Store
- **Context**: The dashboard requires high-speed aggregated trending metrics.
- **Decision**: Pre-calculate aggregates using PostgreSQL Materialized Views.
- **Rationale**: Standing up an OLAP database (ClickHouse) or a Redis cache introduces dual-write complexities.
- **Tradeoffs**: Data is slightly stale (refreshed periodically) rather than strictly real-time.
- **Consequences**: Kept the architecture strictly within a single storage engine.

### ADR-005: Streamlit vs Next.js
- **Context**: Backend engineers needed to validate the data pipeline visually.
- **Decision**: Deploy Streamlit as a temporary operational layer.
- **Rationale**: Streamlit allows Python engineers to build tables and charts instantly without touching Javascript or managing a Node.js build chain.
- **Tradeoffs**: Unacceptable for consumer-facing traffic (no SEO, high latency, poor mobile responsiveness).
- **Consequences**: Streamlit acts solely as internal validation tooling; Next.js is designated as the future production presentation layer.

---

## Technical Debt

- **Synchronous Enrichment**: Entity extraction heuristics currently run inline during the ingestion loop. This is acceptable for simple regex operations, but prevents the integration of heavy Machine Learning models (like Transformers for Sentiment Analysis), which would block the event loop.
  - *Mitigation Strategy*: Will be resolved alongside the Celery migration.
- **Advisory Locks**: The multi-container scaling mitigation relies on a hardcoded PostgreSQL advisory lock. This is a brittle mechanism prone to session hanging under extreme edge cases.
  - *Why Accepted*: Preferable to deploying a distributed locking mechanism like Redis Redlock for the current scale.

---

## Future Architecture

![Runtime Architecture](../docs/assets/backend_runtime.png)

The architectural end-state roadmap involves decoupling the monolith into targeted execution domains:

1. **Decoupled Orchestration**: Replacing `APScheduler` with a Redis-backed distributed task queue. FastAPI will serve exclusively as the HTTP boundary. Ingestion jobs will be picked up by independent worker nodes, allowing infinite horizontal scaling.
2. **Event-Driven ML Enrichment**: Introducing a Kafka/PubSub topic. Once an article lands in PostgreSQL, an event will trigger asynchronous ML workers to perform Named Entity Recognition and update the database retroactively.
3. **Edge Presentation**: Deprecating the Streamlit container entirely in favor of a statically generated Next.js application served via Vercel or an edge CDN, shifting the rendering burden completely off the internal network.
