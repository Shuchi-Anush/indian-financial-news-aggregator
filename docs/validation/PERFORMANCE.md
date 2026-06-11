# Performance Validation

## Intent
Ensure that reads operate in $O(1)$ time, and writes do not lock the active table.

## Validation Criteria
### 1. N+1 Queries
We intentionally **do not** use SQLAlchemy `lazy="select"`. If a relationship is required (e.g., fetching the `FeedSource` attached to an `Article`), it must be requested explicitly via `selectinload()`. The API routers map pure domains, preventing unexpected lazy loads during serialization.

### 2. GIN Index Updates
The `search_vector` is computed via `to_tsvector`. 
- **Validation**: Ensure bulk inserts map `search_vector` updates optimally. PostgreSQL handles this via `fastupdate=on` by default.

### 3. Memory Bound Validation
- `aiohttp` concurrency is capped via `asyncio.Semaphore` (or `gather` chunking) inside the `RSSCollector`. This ensures we never hold 50 XML responses in memory simultaneously.

## Failure Interpretation
If the endpoint `/articles` exceeds 100ms response time on an empty database, or if memory usage grows monotonically over 24 hours, the `AsyncSession` is leaking or the keyset pagination indices (`published_at DESC`, `id DESC`) were dropped.
