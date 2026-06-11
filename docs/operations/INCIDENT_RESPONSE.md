# Incident Response Protocol

## Incident Classification

### SEV-1: Complete Ingestion Paralysis
**Symptom**: `pipeline_runs_total` ceases incrementing completely, or `articles_failed_total` matches `articles_fetched_total`. No new data enters the system.
**Probable Root Causes**:
- Global DNS failure or upstream ISP blocking the backend server IP.
- PostgreSQL entirely out of disk space, rejecting `INSERT`.
- Unhandled Exception breaking the APScheduler execution loop entirely.

**Response Procedure**:
1. Check container logs immediately: `docker compose logs --tail 50 backend`.
2. Inspect disk capacity of the DB volume: `df -h`.
3. If the loop is dead due to a memory issue, execute an emergency restart: `docker compose restart backend`.

### SEV-2: Degraded Ingestion (Circuit Breaker Spikes)
**Symptom**: One or more sources transition their metric gauge to `OPEN` state.
**Probable Root Causes**:
- The target publisher altered their XML schema completely (breaking the feed parser).
- The target publisher IP-banned the aggregator (HTTP 403 Forbidden).
- Rate limits triggered (HTTP 429).

**Response Procedure**:
1. Identify the failed source via `/admin/pipeline/status`.
2. Wait out the circuit breaker timeout.
3. If it persists, fetch the raw payload manually (`curl -A "AggregatorBot" <feed_url>`) to confirm if the ban is IP-based or format-based.

### SEV-3: Query Latency Spikes
**Symptom**: `/articles` or `/analytics/trending` endpoints take >2 seconds to respond.
**Probable Root Causes**:
- High volume of `INSERT` statements executing concurrently while an export streaming request is running.
- Materialized View is actively refreshing (`REFRESH MATERIALIZED VIEW`), locking read operations against it.

**Response Procedure**:
1. Abort long-running exports via proxy termination (nginx/loadbalancer).
2. Wait for the pipeline run to conclude.
