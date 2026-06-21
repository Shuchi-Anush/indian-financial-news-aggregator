# Backend Stabilization & Production Readiness Audit
**Date:** 2026-06-21  
**Target:** `v1.3.2-feed-expansion-complete`  
**Role:** Principal Engineer / Technical Lead

---

## TASK 1 — REPOSITORY TRUTH AUDIT

I have verified the repository firsthand. **The previous reviewers were wrong.** They claimed features were missing that actively exist in the codebase. 

| Finding | Exists? | Status | Evidence |
| ------- | ------- | ------ | -------- |
| Alembic | YES | ✅ Active | `migrations/versions/21af7d79c2f7_initial_schema.py` |
| Search | YES | ✅ Active | `articles.search_vector` GIN index + `q` param in `/articles` |
| Pagination | YES | ✅ Active | Keyset (Zero-Offset) cursor pagination in `articles.py` |
| Exports | YES | ✅ Active | CSV/Excel streaming endpoints in `articles.py` |
| Metrics | YES | ✅ Active | `prometheus_client` in `metrics.py` |
| Circuit Breakers | YES | ✅ Active | `CircuitBreakerState` enum and logic in `repository.py` |
| Advisory Locks | YES | ⚠️ Partial | `pg_try_advisory_lock` exists in `repository.py`, but is not wired to the global scheduler. |
| Materialized Views | YES | ✅ Active | `hourly_trends_mv` and `sentiment_summaries_mv` |
| Health Endpoints | YES | ✅ Active | `/admin/pipeline/status` and `/admin/sources/health` |
| Tests | YES | ⚠️ Weak | Export/Filter tests exist, but core pipeline lacks coverage. |
| Docker Deployment | YES | ✅ Active | Multi-stage `Dockerfile` (using `uv`) and `docker-compose.prod.yml` |

---

## TASK 2 — P0 / P1 / P2 ISSUE IDENTIFICATION

### P0 (Must fix before scaling/launch)
1. **In-Memory Deduplication Bottleneck:** `repository.py` blindly fetches 100,000 URLs and hashes into a Python memory dictionary for deduplication. 
   - *Impact:* Docker Out-of-Memory (OOM) crashes at scale. Bypassed duplicates if total articles exceed 100k.
   - *Risk Level:* Critical.
   - *Effort:* Low.
   - *Files:* `repository.py`, `deduplicator.py`.
2. **Container-Level Scheduling Lock:** `ingestion_jobs.py` uses an `asyncio.Lock()`.
   - *Impact:* Completely prevents horizontal scaling. If you deploy 2 API replicas, both will trigger ingestion simultaneously and overwhelm external feeds.
   - *Risk Level:* High.
   - *Effort:* Low.
   - *Files:* `ingestion_jobs.py`.

### P1 (Should fix before next release)
1. **Admin API Lacks Auth:** `/admin/*` routes expose sensitive pipeline health and failure data without a token.
   - *Impact:* Data leakage.
   - *Risk Level:* Medium.
   - *Effort:* Low.
   - *Files:* `api/routes/admin.py`.
2. **Dead Legacy Code:** Empty wrapper classes remain after the `BaseRSSCollector` factory refactor.
   - *Impact:* Architectural confusion and maintainability drag.
   - *Risk Level:* Low.
   - *Effort:* Trivial.
   - *Files:* `collectors/rss/livemint.py`, etc.

### P2 (Can wait)
1. **Background Tasks for Exports:** Excel export uses `BackgroundTasks` to delete the file, which is fine for MVP, but a dedicated worker (like ARQ/Celery) is better for heavy files.
2. **Test Coverage:** Core pipeline tests are missing.

---

## TASK 3 — DEDUPLICATION REVIEW

**1. Does it load excessive rows?** YES. `stmt = select(Article.url, Article.content_hash).limit(100000)` loads 100k rows into memory on every pipeline run.
**2. Can duplicates bypass?** YES. If an article is the 100,001st oldest, it drops out of the cache and will be ingested again.
**3. Does it scale?** NO. It is O(N) memory scaling.
**4. Safest replacement:** Database-level Batch Lookup.

**Proposed Flow:**
Instead of loading all historical hashes into memory, the `Deduplicator` should take the incoming batch of 50 new articles, extract their hashes/URLs, and perform a single `SELECT url, content_hash FROM articles WHERE url IN (...) OR content_hash IN (...)`. 

**Urgency:** P0.

---

## TASK 4 — SCHEDULER & LOCKING REVIEW

**1. Safe for single-node deployment?** Yes. The `asyncio.Lock()` successfully prevents overlapping jobs within one Python process.
**2. Safe for multiple replicas?** NO. The lock is process-local.
**3. Is asyncio lock sufficient today?** Yes, if you strictly restrict `docker-compose` to 1 backend container.
**4. Should advisory lock be wired in now?** YES. You already wrote `pg_try_advisory_lock` in `repository.source_lock`. You simply need to wrap `_run_pipeline()` in `ingestion_jobs.py` with a global PostgreSQL lock (e.g., hash of "global_ingestion_lock").

---

## TASK 5 — TECHNICAL DEBT ELIMINATION

**DELETE:**
- `backend/src/app/collectors/rss/businessstandard.py`
- `backend/src/app/collectors/rss/cnbctv18.py`
- `backend/src/app/collectors/rss/economictimes.py`
- `backend/src/app/collectors/rss/livemint.py`
- `backend/src/app/collectors/rss/moneycontrol.py`
- `backend/src/app/collectors/rss/sebi.py`

**REFACTOR:**
- `backend/src/app/orchestration/ingestion_jobs.py` (Wire Postgres lock)
- `backend/src/app/processors/deduplicator.py` (Batch DB lookup)

**KEEP:**
- `backend/src/app/collectors/rss/base_rss.py`

---

## TASK 6 — DATABASE REVIEW

**Slow Queries:** `api/routes/admin.py` executes exact counts (`select(func.count(ArticleEntity.id))`). In PostgreSQL, `COUNT(*)` performs sequential or index scans. At millions of rows, this API endpoint will severely lag.
**Improvement:** Replace exact counts with `pg_class.reltuples` estimations for massive tables.

**Schema:** The schema is excellent. GIN indexing is correct. `on_conflict_do_nothing` is perfect for idempotent ingestion.

---

## TASK 7 — API REVIEW

**Frontend Readiness:** HIGH. The `articles.py` router provides everything a modern Next.js 15 App Router needs:
- `cursor` for infinite scrolling.
- `q` for Debounced search.
- `source` and `date_from`/`date_to` arrays for sidebar filtering.

**Missing Capabilities:** Absolutely none for the public frontend. The admin frontend needs a basic `Depends(verify_api_key)`.

---

## TASK 8 — OPERATIONS REVIEW

- **Docker:** Superb `uv` implementation and non-root execution context.
- **Compose:** Health checks successfully orchestrate startup order.
- **Risks:** The `postgres_data_prod` volume has no backup strategy. If the Docker volume is pruned, the database is entirely lost. 
- **Easy Win:** Add a simple `pg_dump` cron job container to `docker-compose.prod.yml`.

---

## TASK 9 — TESTING REVIEW

**Test Coverage Matrix:**

| Area | Status | Priority |
| :--- | :--- | :--- |
| Export Pipelines | ✅ Covered | Low |
| Keyset Pagination | ✅ Covered | Low |
| Article Normalizer | ❌ Not Covered | High |
| Hashing / Dedup | ❌ Not Covered | High |
| API Routes | ❌ Not Covered | High |

**Prioritize missing tests:** The pure functions (`ArticleNormalizer`, `compute_content_hash`) should be unit tested immediately. They require zero mocking.

---

## TASK 10 — FRONTEND READINESS REVIEW

**Can frontend begin immediately?**
**YES.** 

The API contracts (`GET /articles`, `GET /articles/{id}`) are mature, feature-complete, and stable. The P0 backend issues (scheduler locks and dedup memory limits) are strictly internal pipeline issues. They will not change the JSON schema sent to Next.js. 

---

## TASK 11 — FINAL CLEANUP PLAN (Backend Stabilization Sprint)

| Step | Action | Files | Effort | Risk |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Delete legacy wrapper collectors. | `collectors/rss/*.py` | Trivial | None |
| **2** | Add basic API key auth to `/admin` routes. | `api/routes/admin.py` | Low | None |
| **3** | Replace in-memory `get_recent_candidates` with batch SQL lookup. | `repository.py`, `deduplicator.py` | Medium | Medium |
| **4** | Replace `asyncio.Lock()` with global `pg_try_advisory_lock`. | `ingestion_jobs.py` | Low | Low |
| **5** | Replace `COUNT(*)` with `pg_class` estimation. | `admin.py` | Low | Low |

---

## TASK 12 — FINAL VERDICT

1. **Is the backend ready for frontend development?** YES. The API contract is frozen and excellent.
2. **What absolutely must be fixed first?** In-memory deduplication and the local `asyncio.Lock()`.
3. **What can wait until v1.5.0?** Kafka, Redis, ML pipelines, advanced analytics.
4. **What should never be built?** Kubernetes manifests, Microservices (the monolith is perfect).
5. **What would a Principal Engineer criticize today?** O(N) memory scaling in deduplication and the single-node scheduler lock.
6. **What would a professor praise today?** Pure functions, domain-driven design, and strict SQLAlchemy 2.0 typing.
7. **What would a recruiter notice today?** The multi-stage `uv` Dockerfile and Prometheus metrics.

### FINAL DECISION: GO

**GO** for Next.js frontend development. 
The backend P0 issues can and should be fixed in parallel with frontend scaffolding, as they will not alter the REST API contracts.
