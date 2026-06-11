# Operational Runbook

## Overview
This document is intended for SREs and Platform Engineers debugging the live state of the aggregator.

## Debugging Workflows

### 1. Ingestion Pipeline Freezes
**Symptom**: New articles stop appearing, but API remains online.
**Probable Root Causes**:
- APScheduler died or threw an unhandled exception.
- The PostgreSQL advisory lock (`pg_try_advisory_lock`) was orphaned and never released by a crashed worker.
- Target RSS feeds are tarpitting the HTTP client (slow-loris), consuming all async workers.

**Debugging Commands**:
Check pipeline metrics:
```bash
curl http://localhost:8000/metrics | grep pipeline_runs_total
```
Check pipeline admin status:
```bash
curl http://localhost:8000/admin/pipeline/status
```

**Recovery Procedure**:
Restart the backend container to clear the asyncio loop state. PostgreSQL will drop the advisory lock when the TCP session dies.

### 2. Export Overload Handling
**Symptom**: Database query latency spikes and memory warnings appear during a user's CSV export request.
**Probable Root Causes**:
- Bypassed limits on keyset retrieval size.

**Recovery Procedure**:
The export stream uses FastAPI `StreamingResponse`. In severe lockups, restart Uvicorn. The `max_limit` constraint on the router enforces a strict 10k upper bound natively.

### 3. Materialized View Issues
**Symptom**: Analytics dashboards (`/analytics/trending`) show stale data from hours ago.
**Probable Root Causes**:
- The `REFRESH MATERIALIZED VIEW` command failed silently during the ingestion completion cycle.
- The pipeline run itself aborted midway, skipping the refresh phase entirely.

**Recovery Procedure**:
Manually invoke a refresh against the DB:
```sql
REFRESH MATERIALIZED VIEW hourly_trends_mv;
```
