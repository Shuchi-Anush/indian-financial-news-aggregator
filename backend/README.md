# Backend Engineering Overview

The backend module represents the core execution environment of the Indian Financial News Aggregator. 

## Module Structure
- `src/app/api`: HTTP boundaries, FastAPI routers, Pydantic DTOs.
- `src/app/core`: Lifespan hooks, environment loaders, structured logging, middleware, exceptions.
- `src/app/db`: Connection pools, Alembic context, SQLAlchemy setup.
- `src/app/domain`: Agnostic core entities.
- `src/app/models`: SQLAlchemy ORM definitions and materialized view schemas.
- `src/app/orchestration`: Async schedulers, ingestion loops, and Prometheus metric state.
- `src/app/services`: Circuit breakers, feed fetching, text enrichment, exports.

## Execution Lifecycles

### FastAPI Lifespan
We use the modern async `@asynccontextmanager` lifespan event. 
1. `initialize_database()` confirms Postgres reachability.
2. `start_scheduler()` mounts the background tasks.
3. Upon shutdown, `stop_scheduler()` and `dispose_engine()` cleanly sever pending states.

### Scheduler Lifecycle & Advisory Locking
`APScheduler` executes the `run_ingestion_cycle` job inside the event loop. To prevent catastrophic state overlaps (especially if scaling instances or restarting mid-fetch), we rely on two gates:
- `max_instances=1, coalesce=True` inside APScheduler config.
- PostgreSQL Advisory Locks (`pg_try_advisory_lock`) in the Repository boundary to guarantee zero concurrent pipeline collisions across horizontally scaled workers.

### Repository Pattern Enforcement
We strictly segregate database I/O from business logic. The `PersistenceRepository` exposes only abstract persistence behaviors (`save_articles`). Services like `RSSCollector` do not `import sqlalchemy`.

### Keyset Pagination
All paginated API routes use Zero-Offset Keyset Pagination. 
Instead of `LIMIT 50 OFFSET 1000`, we require the last seen cursor and query `WHERE (published_at, id) < (cursor_date, cursor_id) ORDER BY published_at DESC`. This mitigates memory scan degradation inherent in deep offsets.

### Materialized Views
`hourly_trends_mv` and `sentiment_summaries_mv` provide high-speed $O(1)$ statistical reads.
**Limitation**: They are refreshed synchronously post-ingestion.

## Known Bottlenecks
- **Memory Consumption**: If a feed throws 10,000 massive articles, the `aiohttp` gathering phase buffers the XML into memory before normalization.
- **Export Overload**: The `GET /articles/export/csv` route streams data chunks, but is bounded to a maximum of 10,000 articles to avoid network timeout and DB cursor starvation.
