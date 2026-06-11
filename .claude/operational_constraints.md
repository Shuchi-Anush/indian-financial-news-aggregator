# Operational Constraints

## Startup
- The app binds to `0.0.0.0:8000`.
- The Lifespan event `initialize_database()` will intentionally crash the app if PostgreSQL is unreachable. This is correct behavior. Do not "fix" it by silently ignoring DB failures.

## Memory Bound
- Exports use `StreamingResponse` with an absolute upper bound of 10,000 items. Do not raise this bound without consulting the memory limits of the container.

## Locking
- The system prevents concurrent APScheduler overlap by using PostgreSQL Advisory Locks (`pg_try_advisory_lock`). Do not remove this mechanism. It enables horizonal scaling of the backend container without duplicating ingestion runs.
