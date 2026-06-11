# Known Limitations & Scalability Thresholds

This document explicitly calls out the architectural limits of the current implementation and prescribes future mitigation paths.

## 1. Current Scale Limits
- **Single Node Capacity**: The backend relies entirely on the compute and disk IO of a single PostgreSQL node. There is no read-replica routing or sharding implemented.
- **Ingestion Limit**: Bounded by memory. If a single pipeline execution pulls 100 feeds with 5,000 articles each, the `aiohttp` buffer will consume roughly 1-2GB of RAM during the `gather()` phase before garbage collection kicks in.

## 2. GIN Index Update Costs
The `search_vector` field uses a `TSVECTOR` generation and a GIN index.
- **Limitation**: GIN indexes incur a severe write-penalty. If the system is hit with 50,000 sudden unique inserts, the active write locks may cause lock-wait timeouts for API readers.
- **Future Strategy**: Move text searching out of Postgres into OpenSearch/Elasticsearch, leaving Postgres purely for relational joins.

## 3. Materialized View Refresh Limitations
The `REFRESH MATERIALIZED VIEW` command is synchronous and locks the view for reads.
- **Limitation**: At 1M+ rows, the refresh blocks API requests hitting `/analytics/trending`.
- **Future Strategy**: Switch to `REFRESH MATERIALIZED VIEW CONCURRENTLY`. This requires adding a unique index to the MV output, which complicates windowed aggregations but preserves zero-downtime reads.

## 4. Exporter Limitations
The `/articles/export/csv` streaming route binds directly to a SQLAlchemy server-side cursor.
- **Limitation**: While it streams effectively, the DB cursor remains open for the duration of the HTTP download. If a client downloads on a 56kbps connection, they hold a DB connection pool slot hostage.
- **Future Strategy**: Implement an asynchronous export task that writes to AWS S3 and returns a presigned URL, rather than streaming over FastAPI.

## 5. PostgreSQL Table Partitioning Strategy
The `articles` table will eventually experience B-Tree degradation on the `url` unique constraint as the table eclipses available RAM.
- **Future Strategy**: Implement `PARTITION BY RANGE (published_at)`. This ensures that only the current month's B-Tree indices remain in hot memory, dramatically speeding up `ON CONFLICT DO NOTHING` operations.
