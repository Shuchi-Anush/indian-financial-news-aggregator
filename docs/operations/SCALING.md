# Scaling the Aggregator

The current architecture is a modular monolith containing both API serving and background ingestion.

## Identifying the Need to Scale
- **Memory Starvation**: FastAPI workers crash under `MemoryError` when buffering huge XML bodies.
- **CPU Starvation**: GIN Index building (during search_vector population) consumes 100% CPU on PostgreSQL inserts, degrading API read speeds.

## Scalability Limits
- **Single-Node DB Constraints**: The `ON CONFLICT (url) DO NOTHING` heavily relies on a massive `B-Tree` index. Beyond 10M rows, this index exceeds active RAM capacity, severely slowing disk I/O.
- **Scheduler Limitations**: APScheduler is bound to a single container. If you replicate the container across 3 Kubernetes pods, you will have 3 independent schedulers. (Mitigated currently by `pg_try_advisory_lock`, meaning 2 out of 3 will silently skip the job, but it is an anti-pattern for long-term distributed task execution).

## Future Evolution Path
When the system exceeds vertical scale bounds:

### 1. Extract Ingestion
- Disable `start_scheduler()` in the FastAPI lifespan.
- Move `run_ingestion_cycle` into a Celery Worker or Airflow DAG.
- Deploy the worker pool independently from the API pods.

### 2. Database Partitioning
Execute native PostgreSQL range partitioning by time.
```sql
CREATE TABLE articles_2026_q1 PARTITION OF articles
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
```
This forces the B-Tree index to stay small and memory-resident for the active writing quarter.

### 3. Read Replicas
Route `GET /articles` to a read-replica. Ensure `PersistenceRepository` leverages a router logic to pick connections based on write/read intentions.
