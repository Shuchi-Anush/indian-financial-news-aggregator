# READ API Architecture Implementation Complete

The production-grade READ API architecture layer has been fully implemented, adhering to the required architecture boundaries and keyset pagination constraints.

## Changes Made

### 1. Database & Models (Phase 1)
- **`Article` Model Hardening**:
  - Added a generated `tsvector` column (`search_vector`) to compute and store search indices natively in PostgreSQL.
  - Set `lazy="raise"` on the `feed_source` relationship to prevent accidental N+1 queries.
  - Added necessary composite indexes for optimized keyset pagination and source filtering: `(published_at DESC, id DESC)` and `(source_name, published_at DESC)`.
- **Alembic Migration**:
  - Auto-generated and successfully applied the Alembic migration `search_vector_and_indexes` against the PostgreSQL database.

### 2. Schemas & Contracts (Phase 2)
- **Common Schemas**:
  - Created `CursorPage` and `PaginationMeta` for generic paginated responses.
- **Entity Schemas**:
  - `ArticleListItem`: Lightweight projection without content body.
  - `ArticleDetail`: Full representation with text content.
  - `ArticleFilters`: Strongly typed filters structure.
  - `SourceResponse` and `PipelineRunResponse` created mapping to domain models.

### 3. Cursor Engine (Phase 3)
- Implemented `CursorEngine` in `src/app/utils/cursor.py` to handle opaque, URL-safe base64 encoding and decoding.
- The cursor natively embeds the keys `p` (published_at), `i` (id), and optionally `r` (ts_rank) for deterministic fast keyset pagination.

### 4. Repository Layer (Phase 4)
- **`ArticleRepository`**:
  - Implemented `list_articles` with explicit column projection (no `.body` or `.summary` loaded).
  - Full keyset pagination support: Handles complex sorting logic `(ts_rank DESC, published_at DESC, id DESC)` for searches, and `(published_at DESC, id DESC)` for default listing.
  - Implemented `get_by_id`.
- **`PipelineRepository`** & **`SourceRepository`**: Add### Read API and Export Platform
- Keyset pagination for `GET /api/articles` to support infinite scrolling securely.
- CSV/Excel stream-based exporters using efficient yield-based chunking.
- Date, source, and text-based query filtering.

### Orchestration and Resilience Layer
- **APScheduler Integration**: Runs ingestion cycles on an asynchronous background interval tightly coupled to the FastAPI lifespan.
- **Ingestion Run Locking**: PostgreSQL `pg_try_advisory_lock` protects against overlap across multiple Docker replicas.
- **Retry Policy Engine**: Implemented `_fetch_with_retry` in `base_rss.py` covering TRANSIENT (jittered exponential backoff), RATE_LIMITED (reads `Retry-After`), and PERMANENT mapping.
- **Circuit Breaker System**: Automatically skips sources marked as `OPEN` if they experience repeated unrecoverable failures.
- **Admin Dashboard APIs**: Read routes (`/admin/pipeline/status`, `runs`, `sources/health`) to give an operational view of system health.
- **Metrics Expansion**: Exposed pipeline run durations and source health states.cles`, `sources`, and `pipeline_runs`.
- Registered all routers gracefully in `src/app/main.py`.
- Services correctly decouple Repositories and Routers by handling cursor generation, `limit+1` truncation (`has_more`), and mapping Database Rows to Pydantic models.

## Validation Results
- `mypy` strict checks pass.
- `ruff` auto-fixes pass cleanly across the new services, repositories, schemas, and routes.
- Database starts up via Docker seamlessly. The FastAPI application boots properly and binds without failure.
