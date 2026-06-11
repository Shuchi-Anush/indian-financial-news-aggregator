# Database Validation

## Intent
Validate that PostgreSQL transaction isolation, advisory locking, and Alembic downgrades function as designed.

## DB Validation Script
`backend/scripts/test_db_validation.py` executes:
1. **Concurrent Insertion Testing**: Launches 50 parallel `asyncio.gather` tasks attempting to insert overlapping data to verify `ON CONFLICT DO NOTHING` prevents `UniqueViolation` crashes.
2. **Advisory Locking**: Spawns multiple workers competing for `pg_try_advisory_lock`. Ensures that only worker 0 succeeds while worker 1 and 2 abort cleanly without blocking.
3. **Rollback Behavior**: Forces a raw SQL syntax error mid-transaction, proving that SQLAlchemy successfully issues `ROLLBACK` and the connection pool remains healthy.

## Failure Interpretation
- If the concurrent insertion test fails with `IntegrityError`, the deduplication hash logic or the DB schema unique constraint was altered.
- If advisory locking fails, `APScheduler` is at risk of spawning overlapping ingestion jobs, duplicating network calls and CPU burn.
