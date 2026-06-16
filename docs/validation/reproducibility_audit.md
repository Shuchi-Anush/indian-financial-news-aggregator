# Production Readiness & Reproducibility Audit

## PHASE 1 — Reproducibility Audit
Starting from a clean clone, the environment was destroyed and completely reset (`docker compose down -v`, followed by removing all remaining containers). A fresh `docker compose up -d` was executed to simulate a new developer cloning the repository.

| Verification Step | Result | Evidence / Log Output |
|-------------------|--------|------------------------|
| **`docker compose up -d`** | ✅ PASS | Containers `finnews-db` and `finnews-backend` built and started cleanly. Healthchecks pass. |
| **PostgreSQL Initialization** | ✅ PASS | Container logs show `database system is ready to accept connections`. |
| **Alembic Migrations** | ❌ FAIL | `psql -c "\dt"` returned `Did not find any relations.` No automatic migration trigger exists in the backend boot sequence. |
| **Application Startup** | ✅ PASS | FastAPI / Uvicorn starts correctly and binds to port `8000`. |
| **Scheduler Startup** | ✅ PASS | APScheduler starts correctly: `Added job "run_ingestion_cycle" to job store`. |
| **Feed Source Initialization**| ❌ FAIL | The `feed_sources` table does not exist. Even if it did, there is no automatic seeding mechanism on startup. |
| **Analytics View Init.** | ❌ FAIL | The materialized views (`hourly_trends_mv`, `sentiment_summaries_mv`) are missing and not tied to standard Alembic migrations. |
| **First Ingestion Cycle** | ❌ FAIL | Fails because tables do not exist and no active feeds are populated in the database. |

---

## PHASE 2 — Manual Intervention Detection
The following operations currently require manual execution to achieve a functioning pipeline.

| Manual Step | Why Required | Risk | Required Fix |
|-------------|--------------|------|--------------|
| `alembic upgrade head` | Migrations do not run automatically on backend startup. | Without it, any API request or scheduled job fails with `relation does not exist` errors. | Add an `entrypoint.sh` script to the backend Dockerfile that runs migrations before `uvicorn`. |
| `python scripts/seed_feeds.py` | The database starts empty. No RSS feeds are tracked out of the box. | The scheduler will fire every cycle, find zero active sources, and exit without fetching anything. | Add a data migration in Alembic or execute the seed script automatically in `entrypoint.sh`. |
| `CREATE MATERIALIZED VIEW` | Alembic `upgrade head` generates standard tables, but custom SQL for materialized views is missing. | The pipeline crashes at the end of the ingestion cycle when attempting to `REFRESH MATERIALIZED VIEW`. | Create a custom Alembic migration step `op.execute("CREATE MATERIALIZED VIEW...")`. |
| Start Frontend | The default `docker-compose.yml` only provisions `db` and `backend`. | Developers will have no UI to view the aggregator unless they manually run the streamlit app or use the `prod` compose file. | Merge the `frontend` service into the default `docker-compose.yml` for local dev. |

---

## PHASE 3 — Clean Clone Validation
**Result:** **FAIL**  
A completely new machine **cannot** reach `feed_sources > 0` and `articles > 0` automatically.

**Exact Blocker:** The database is an empty shell on startup.  
**Root Cause:** The `finnews-backend` container directly invokes `uvicorn` as its command without a pre-boot `entrypoint.sh` lifecycle script. Furthermore, required data (`feed_sources`, Materialized Views) rely entirely on standalone python/SQL scripts run by human operators.  
**Minimal Fix:**  
Create an `entrypoint.sh` in the backend:
```bash
#!/bin/sh
uv run alembic upgrade head
uv run python scripts/seed_feeds.py
# (Include materialized view creation in an alembic revision)
exec "$@"
```

---

## PHASE 4 — Operational Readiness Audit

| Area | Current Status | Risks & Severity | Recommended Next Action |
|------|----------------|------------------|--------------------------|
| **1. Backend** | FastAPI starts cleanly and uses async architectures. | **Low:** Safe to run, but lacks an entrypoint. | Add `entrypoint.sh`. |
| **2. Database** | PostgreSQL 16 is robustly configured with volumes. | **High:** Empty schema on boot breaks everything. | Automate Alembic migrations on startup. |
| **3. Scheduler** | APScheduler is integrated natively into the FastAPI lifecycle. | **Medium:** Graceful shutdown is not bounded tightly enough in long-running jobs. | Add hard timeouts to the shutdown lifecycle hook. |
| **4. RSS Ingestion** | Highly resilient. Quality Gates and HTTP handling (403s/retries) work well. | **Medium:** Fails silently on start if `feed_sources` is empty. | Automate database seeding. |
| **5. Deduplication**| Correctly relies on URL hashing and `articles` table constraints. | **Low:** Functions correctly once schema is present. | None. |
| **6. Search** | Relies on PostgreSQL `tsvector`. | **Medium:** Performance will degrade without Gin indexes on `search_vector`. | Ensure Gin indexes are defined in SQLAlchemy models. |
| **7. Analytics** | Relies on materialized views. | **High:** Views crash the pipeline if missing. | Add materialized views to Alembic migrations. |
| **8. Export** | Depends on API endpoints. | **Low:** Safe. | None. |
| **9. Frontend** | Streamlit app exists but is disjointed from local dev environment. | **High:** Devs clone and see no UI. | Add `frontend` to default `docker-compose.yml`. |
| **10. Docker** | `Dockerfile` is optimized and uses `uv`. | **High:** Lacks startup orchestration (entrypoints). | Introduce standard Docker entrypoints. |
| **11. Monitoring** | Healthcheck endpoints (`/health`) exist. | **High:** No Prometheus metrics or Grafana dashboards for a "Platform Engineer" product. | Integrate `prometheus_client` and expose `/metrics`. |
| **12. Logging** | `structlog` provides structured JSON logging. | **Medium:** Logs stream to stdout but are not aggregated. | Sufficient for now; Loki/ELK is a future tier. |
| **13. Security** | Non-root containers implemented; pinned versions. | **Medium:** No API authentication/rate-limiting present. | Add simple API key/CORS policies. |
| **14. Backup** | Local volume mounts only. | **High:** Data loss on VPS loss. | Add a daily pg_dump cron sidecar. |

---

## PHASE 5 — Evidence-Based Gap Report

### A. Professor Demo Readiness Score: 6/10
**Justification:** The core architecture (FastAPI, AsyncPG, APScheduler, UV, Docker) is excellent and modern. The actual Python logic is highly robust. However, a professor cloning the repo and typing `docker compose up` will see an empty database, no UI, and silent failures, which deeply hurts the first impression.

### B. Single VPS Production Readiness Score: 4/10
**Justification:** While the `docker-compose.prod.yml` adds Nginx and Frontend, it still suffers from the "empty database on boot" fatal flaw. Furthermore, running this on a VPS currently lacks automated backups, metrics dashboards (Prometheus), and log aggregation.

### C. Public Internet Deployment Readiness Score: 2/10
**Justification:** Beyond the VPS issues, exposing this to the public internet without rate-limiting, CORS protections, API authentication, or HTTPS (Nginx is currently port 80 only) is dangerous. 

---

## PHASE 6 — Roadmap

### Tier 1 — Must Fix Before GitHub Release (Reproducibility)
1. Write a `backend/entrypoint.sh` to run `alembic upgrade head`.
2. Generate an Alembic revision to create the Materialized Views.
3. Generate an Alembic data migration (or trigger `seed_feeds.py` in entrypoint) to populate the initial 5 feeds automatically.
4. Add the `frontend` service to the default `docker-compose.yml`.

### Tier 2 — Must Fix Before Professor Demonstration (Observability)
1. Integrate `prometheus_client` to expose `/metrics` for ingestion counts, duration, and error rates.
2. Ensure Streamlit connects flawlessly without manual `.env` configuration.
3. Clean up backend logs to reduce Uvicorn noise and highlight Ingestion milestones.

### Tier 3 — Must Fix Before Public Deployment (Security & Resiliency)
1. Add Nginx TLS/SSL configuration.
2. Add rate-limiting middleware to FastAPI.
3. Add an automated `pg_dump` sidecar container for backups.

### Tier 4 — Future Research Platform Enhancements
1. ELK or Loki stack for log aggregation.
2. Kafka/RabbitMQ decoupling of the ingestion scheduler from the FastAPI web worker.
3. Deep Learning entity extraction models replacing regex logic.
