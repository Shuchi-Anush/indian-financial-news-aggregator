# System Architecture Walkthrough

This document provides a deep architectural analysis of the Indian Financial News Aggregator. It serves as a systems-design case study, explaining the explicit engineering tradeoffs, the data lifecycle boundaries, and the reliability mechanisms that govern the platform.

## 1. Architectural Goals

The platform was designed against the following constraints:
- **Resilience**: The system must survive poisoned external payloads and unpredictable network conditions without halting.
- **Idempotency**: The ingestion pipeline must be able to repeatedly process overlapping time windows without corrupting data or creating duplicates.
- **Flat Latency**: The system must serve millions of records to API consumers with constant-time ($O(1)$) latency.
- **Modularity**: The boundary between data fetching, normalization, and persistence must remain strictly decoupled.

## 2. System Architecture

![System Architecture](assets/system_architecture.png)

### What does this component do?
The overarching system orchestrates the complete lifecycle of financial news data—from raw external XML to normalized, searchable API payloads. It is deployed as a suite of Docker containers coordinated via Nginx.

### Why does it exist?
To decouple the erratic nature of network scraping from the high-availability requirements of API serving.

### How does it interact?
Nginx acts as the edge boundary, routing consumer requests to the FastAPI backend or the operational dashboard. The backend independently interfaces with external RSS providers and the PostgreSQL persistence layer.

## 3. Runtime Architecture

![Backend Runtime](assets/backend_runtime.png)

### What does this component do?
The backend runtime consolidates asynchronous API request serving (Uvicorn) and background job orchestration (`APScheduler`) within a single, unified Python process.

### Why does it exist?
To minimize deployment complexity during the initial rollout. By embedding the scheduler within the ASGI event loop, we avoided the operational burden of standing up dedicated Celery workers and Redis brokers.

### What tradeoffs were made?
Embedding the scheduler prevents horizontal scaling of the ingestion tier. If multiple backend containers are deployed currently, they will redundantly execute the same fetching jobs.

## 4. Ingestion Pipeline

![Pipeline Flow](assets/pipeline_flow.png)

### What does this component do?
The pipeline represents the strict linear progression of data. It ensures that raw payloads are explicitly fetched, normalized, mapped to canonical schemas, and deterministically enriched.

### Why does it exist?
Without an explicit pipeline, parsing logic inevitably bleeds into persistence logic. This strict flow ensures that the database only ever receives validated, well-formed entities.

## 5. Orchestration Model

![Orchestration Pipeline](assets/orchestration_pipeline.png)

### What does this component do?
The `PipelineOrchestrationService` acts as the transaction coordinator. It triggers the `RSSCollector`, iterates through the raw payloads, invokes the normalization logic, and initiates the database session.

### How does it interact?
It sits above the repositories and collectors. It is the only component that dictates when an SQLAlchemy `AsyncSession` commits or rolls back, ensuring atomic logging of pipeline telemetry alongside the data payload.

## 6. Persistence Architecture

![Persistence Flow](assets/persistence_flow.png)

### What does this component do?
The persistence architecture mandates how data physically lands on disk. It handles batching, async session management, and primary collision avoidance.

### Why does it exist?
To prevent database connection starvation and guarantee idempotency. By relying on native PostgreSQL `UPSERT` capabilities, the application avoids memory-heavy "read-before-write" existence checks.

## 7. Database Design

![Database Schema](assets/database_schema.png)

### What does this component do?
The schema organizes the data layer into relational, highly indexed tables (`feed_sources`, `articles`, `pipeline_runs`).

### What tradeoffs were made?
The `articles` table maintains a `tsvector` column. While this increases storage bloat and lightly impacts write speeds, it removes the immense operational complexity of syncing the database state with an external search engine like Elasticsearch.

## 8. Data Lifecycle

The lifecycle of an article follows strict immutability principles:
1. **Raw**: Unstructured XML fetched via HTTP.
2. **Parsed**: Unclean string data mapped to a Pydantic DTO.
3. **Canonical**: Timestamps coerced to UTC, HTML tags stripped, text normalized.
4. **Persistent**: Cryptographic hash generated; stored durably in PostgreSQL.
5. **Served**: Queried via keyset pagination; serialized to JSON over HTTP.

## 9. Reliability Mechanisms

The platform ensures reliability through isolated failure domains. 
If an RSS endpoint is unreachable, the HTTP client throws an exception. This exception is caught locally within the specific feed's ingestion loop. The failure is recorded in the pipeline telemetry, the internal circuit breaker increments its failure count, and the orchestrator seamlessly moves to the next feed source. The API worker remains completely unaffected.

## 10. Deduplication Design

Deduplication logic is offloaded to the database engine.
A SHA-256 hash (`content_hash`) is generated prior to insertion. We execute an `INSERT INTO ... ON CONFLICT (content_hash) DO NOTHING` statement. 
*Why?* Scraping schedules frequently overlap. Instead of pulling 10,000 URLs into backend RAM to check for duplicates, the database engine enforces the constraint at the disk level in fractions of a millisecond.

## 11. Analytics Layer

Analytics computation utilizes PostgreSQL **Materialized Views**.
Instead of running expensive `GROUP BY` aggregates on the live `articles` table on every API request, the system computes these metrics in the background. The FastAPI endpoint simply reads the pre-computed view, ensuring constant-time serving latency.

## 12. Export Architecture

To support massive data extraction without triggering Out-Of-Memory (OOM) killer terminations, the export subsystem streams the data. It utilizes server-side cursors in PostgreSQL to fetch chunks of records, format them into CSV rows, and yield them via FastAPI's `StreamingResponse` directly to the TCP socket.

## 13. Scalability Analysis

- **API Serving**: The backend is completely stateless. It can be replicated indefinitely behind an Nginx load balancer to handle arbitrary read traffic.
- **Database**: PostgreSQL can handle tens of thousands of concurrent reads, particularly given the aggressive use of indexes and keyset pagination.
- **Ingestion**: The embedded scheduler limits the ingestion tier to a single node.

## 14. Bottlenecks

1. **Embedded Scheduler**: Restricts horizontal scaling.
2. **Text Search**: PostgreSQL `tsvector` is fast, but lacks fuzzy matching and semantic understanding compared to Lucene-based indexes.
3. **Memory Buffering**: Extreme edge cases where a single RSS feed payload exceeds 500MB could spike worker RAM during XML parsing.

## 15. Future Evolution

The architectural roadmap dictates two necessary evolutions to achieve hyper-scale:
1. **Transition to Distributed Queues**: Ripping out the embedded `APScheduler` and placing fetch payloads onto a Redis-backed Celery cluster.
2. **Presentation Decoupling**: Deprecating the Streamlit operational dashboard in favor of a statically generated Next.js application, shifting the rendering burden entirely to the client edge.

## 16. Architectural Tradeoffs

**Consistency over Speed**: We strictly wait for database commits before acknowledging pipeline successes. If a crash occurs mid-write, the transaction is rolled back entirely, preventing phantom states.

**PostgreSQL over NoSQL**: While Document stores (MongoDB) easily digest varying XML schemas, we enforced rigid relational schemas. This forces data cleanup to happen at the ingestion boundary, ensuring the API layer never has to parse unstructured data.
