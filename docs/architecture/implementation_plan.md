# Phase 1: Repository & Implementation Audit

Before executing modifications, a complete repository inspection was performed targeting `src/app/*`, `docker-compose.yml`, and the `frontend` directories to determine the actual delta between the "stabilized prototype" and a "production-grade platform."

## 1. Implementation-Grounded Findings

### Observability & Operations (Phase 3 Gaps)
- **Fake Metrics Registry:** `src/app/core/metrics.py` dynamically queries PostgreSQL to generate text-based Prometheus metrics on the fly (e.g., `select func.count(PipelineRun.id)`). It defines a `NoOpRegistry` that silently discards real-time telemetry (like `registry.inc("normalization_errors_total")` seen in `pipeline.py`).
- **Missing API Observability:** There is no middleware tracking API response latency (`http_request_duration_seconds`) or status codes.
- **Weak Health Probes:** `src/app/main.py` exposes a generic `/health` returning `{"status": "ok"}`. It does not separate liveness (`/health/live`) from readiness (`/health/ready`), nor does it actively ping the database or check scheduler thread health.

### Feed Ingestion Resilience (Phase 2 Gaps)
- **Metrics Isolation:** `base_rss.py` uses `httpx` with retries, but because the metrics registry is `NoOpRegistry`, source-level success/failure counts and ingestion latency are completely lost in real-time.
- **Missing Circuit Breaker Sync:** The database tracks `CircuitBreakerState`, but there's no real-time metrics emission for alerting when a source trips OPEN.
- **HTML Sanitization:** `normalizer.py` uses `BeautifulSoup(text, "html.parser").get_text()`, which strips HTML but doesn't sanitize rich text if we ever want to display HTML safely on the frontend.

### Long Duration Stability (Phase 4 Gaps)
- **Unbounded Connection Pools:** `src/app/db/session.py` calls `create_async_engine` without explicit `pool_size`, `max_overflow`, or `pool_timeout`. Under concurrent ingestion and API load, this risks connection starvation.
- **Non-Graceful Scheduler Shutdown:** `src/app/orchestration/scheduler.py` uses `scheduler.shutdown(wait=False)` during FastAPI's lifespan teardown. This forcefully orphans running ingestion tasks, risking partial DB writes and zombie `PipelineRun` records left in a `RUNNING` state indefinitely.
- **No Ingestion Backpressure:** Concurrency is hardcoded via `DEFAULT_PIPELINE_CONCURRENCY` (Semaphore), but memory bounds for massive RSS XML parsing are not enforced.

### Frontend & Deployment (Phase 5 & 6 Gaps)
- **Missing UI:** `frontend/streamlit/` exists but is empty/unimplemented.
- **Deployment Topology:** `docker-compose.yml` lacks an Nginx reverse proxy layer, production environment handling, and centralized volume/logging definitions.

---

## User Review Required

> [!WARNING]
> **Metrics Override:** I will replace the DB-query-based metrics in `metrics.py` with true `prometheus_client` memory registries. This means historical totals will drop from the `/metrics` endpoint unless backfilled, but real-time latency and throughput will become accurate.
> 
> **Shutdown Blocking:** Fixing the scheduler teardown will cause the FastAPI container to wait up to 15 seconds during shutdown to gracefully terminate ingestion jobs. 
> 
> **Do you approve of these strict operational overrides before I begin execution?**

---

## Execution Plan (Phases 2-7)

### Phase 2 — Feed Ingestion Hardening
#### [MODIFY] `src/app/collectors/rss/base_rss.py`
- Enhance `feedparser` error handling and enforce strict timeouts per feed.
- Wire actual Prometheus metrics for latency and payload sizes.

### Phase 3 — Observability & Operations
#### [MODIFY] `src/app/core/metrics.py`
- Strip `NoOpRegistry` and DB-querying logic. Implement `prometheus_client`.
#### [MODIFY] `src/app/core/middleware.py` (New/Modify)
- Add Prometheus request latency timing middleware.
#### [MODIFY] `src/app/main.py`
- Implement `/health/live` (process check) and `/health/ready` (DB ping via `get_engine().execute(text("SELECT 1"))`).

### Phase 4 — Long Duration Stability
#### [MODIFY] `src/app/db/session.py`
- Apply `pool_size=20`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800` to `create_async_engine`.
#### [MODIFY] `src/app/orchestration/scheduler.py` & `src/app/core/startup.py`
- Implement a graceful shutdown loop that waits for `_ingestion_lock` to clear before terminating.

### Phase 5 — Frontend Implementation
#### [NEW] `frontend/streamlit/app.py` & `frontend/streamlit/requirements.txt`
- Build a multi-page Streamlit dashboard (Dashboard, Article Explorer, Source Health).
- Fetch data exclusively via the FastAPI `httpx` client.

### Phase 6 — Deployment & Hosting
#### [NEW] `infra/nginx/nginx.conf`
#### [NEW] `docker-compose.prod.yml`
- Define Nginx reverse proxy routing `/api` to backend and `/` to Streamlit.

### Phase 7 — Final Production Readiness Audit
- Generate a conclusive `artifacts/production_audit_report.md` classifying architectural limits, scaling boundaries, and future migration paths.

## Verification Plan
After every phase:
1. Run `uv sync --frozen`, `uv lock --check`, `uv run ruff check src tests`, `uv run mypy src`, `uv run pytest -q`.
2. Spin up `docker compose up --build -d`.
3. Validate `/health/ready` and `/metrics`.
