# v1.4.0 Implementation Plan: Visibility & Stability Release

**Date:** 2026-06-21  
**Author:** Technical Lead & Principal Architect  

This document outlines the exact execution path for v1.4.0. It prioritizes backend stabilization (eliminating P0 scalability blockers) and the introduction of a Next.js frontend to transform the headless backend into a demonstrable product.

---

## PART 1 — SPRINT STRUCTURE

### Week 1: Backend Stabilization & CI/CD
| Task | Priority | Dependencies | Effort | Risk | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A. Remove Legacy Collectors** | High | None | Low | Low | Clean `collectors/rss/` directory containing only `base_rss.py`. |
| **B. Deduplication Refactor** | P0 | None | High | Medium | Eliminates `LIMIT 100000` OOM risk. Idempotency preserved. |
| **C. Advisory Lock Integration**| P0 | None | Medium| Medium | Prevents multi-node ingestion duplication. |
| **D. Admin Authentication** | P1 | None | Low | Low | API key protection for `/admin` routes. |
| **E. Test Coverage Expansion** | P1 | None | Medium| Low | Tests for core pure functions and DB pipelines. |
| **F. GitHub Actions CI** | P1 | Tasks A-E | Low | Low | Automated Ruff, Pytest, and Docker build checks. |

### Week 2: Next.js Frontend
| Task | Priority | Dependencies | Effort | Risk | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **G. Next.js Scaffolding** | High | None | Low | Low | App Router, Tailwind, TS configured. |
| **H. API Client & Types** | High | None | Low | Low | Fetch/Axios layer mapping to FastAPI contracts. |
| **I. Dashboard (/)** | High | Task H | High | Low | High-density chronological feed. |
| **J. Search Hub (/search)** | High | Task H | Medium| Low | GIN-backed full-text search and filters. |
| **K. Regulatory Desk** | High | Task H | Medium| Low | Distinct UI for SEBI/RBI policy updates. |
| **L. Admin Health Panel** | Med | Task D, H | Low | Low | Read-only pipeline metrics view. |
| **M. Readme Upgrade** | High | Tasks A-L | Low | Low | Recruiter-optimized repository documentation. |

---

## PART 2 — BACKEND STABILIZATION

### Task A — Remove Legacy Collectors
- **Analysis:** I ran `grep_search` across `backend/src`. The classes (`LiveMintRSSCollector`, `SebiRSSCollector`, etc.) are entirely unreferenced. The orchestrator uses `BaseRSSCollector`. 
- **Deletion Plan:** `rm backend/src/app/collectors/rss/{sebi,livemint,moneycontrol,economictimes,businessstandard,cnbctv18}.py`.
- **Validation:** Run `pytest` and `uvicorn` to verify no import errors.

### Task B — Deduplication Refactor
- **Current implementation:** `repository.py` fetches 100k URLs and hashes into memory.
- **Design (Batch Database Lookup):**
  1. `Deduplicator` class is updated to be stateless.
  2. `pipeline.py` extracts a list of `content_hash` and `url` from the current batch of `CanonicalArticle`s.
  3. `repo.get_existing_hashes_and_urls(hashes, urls)` queries PostgreSQL: `SELECT url, content_hash FROM articles WHERE content_hash = ANY(:hashes) OR url = ANY(:urls)`.
  4. The returned set is passed to `Deduplicator.check_duplicate()`.
- **Outcome:** Eliminates O(N) memory scaling while preserving exact idempotency.

### Task C — Advisory Lock Integration
- **Current implementation:** `ingestion_jobs.py` uses `asyncio.Lock()` (process-local).
- **Design:**
  1. Add a globally stable key: `GLOBAL_INGESTION_LOCK_ID = 1001`.
  2. Wrap `_run_pipeline()` with `async with repo.global_advisory_lock(GLOBAL_INGESTION_LOCK_ID):`.
  3. If lock acquisition fails, the scheduler safely skips the cycle (meaning another node is running it).
- **Outcome:** Safe for multiple Docker replicas.

### Task D — Admin Authentication
- **Design:**
  1. Add `ADMIN_API_KEY` to `Settings`.
  2. Create `def verify_admin_key(x_api_key: str = Security(api_key_header))` in `api/dependencies.py`.
  3. Inject `Depends(verify_admin_key)` into the `admin.py` router.

### Task E — Test Coverage Expansion
- **Test Matrix:**
  - `test_normalizer.py`: Assert HTML stripping, date parsing logic.
  - `test_hashing.py`: Assert deterministic SHA-256 output.
  - `test_deduplicator.py`: Assert exact hash/URL match logic.

---

## PART 3 — GITHUB ACTIONS

- **Workflow File:** `.github/workflows/ci.yml`
- **Job Sequence:**
  1. **Lint:** `uv run ruff check .` and `uv run ruff format --check .`
  2. **Test:** `uv run pytest --cov=app` (Requires a running Postgres service container in Actions).
  3. **Build:** `docker build -t finnews-backend:test backend/`
- **Caching Strategy:** Utilize `actions/setup-python` caching and Docker layer caching.

---

## PART 4 — NEXT.JS FRONTEND

**Target:** Next.js 15, TypeScript, Tailwind CSS, App Router.
**Vibe:** Professional financial intelligence terminal (Bloomberg-lite). High density, dark mode default.

### Required Pages
- `/` (Dashboard): Latest news feed, Source Badges, pagination controls.
- `/search` (Search Hub): Debounced full-text search, Source dropdown filters, Date pickers.
- `/regulatory` (Regulatory Desk): A feed locked to SEBI/RBI sources. Articles here use an Amber/Gold visual highlight.
- `/admin/health` (Pipeline Monitoring): Uses the new `ADMIN_API_KEY` to fetch and render system health graphs.

---

## PART 5 — API CONTRACT VALIDATION

**Backend Endpoint → Frontend Consumer Mapping:**
- `GET /articles` → Dashboard (`/`), Search (`/search`), Regulatory (`/regulatory` with `source=sebi`).
- `GET /articles/export/csv` → Export Button on all feeds.
- `GET /admin/pipeline/status` → Admin Health panel.
- `GET /admin/sources/health` → Admin Health panel.

**Validation:** The existing APIs perfectly cover the required UI functionality. Zero new backend endpoints are needed. 

---

## PART 6 — README UPGRADE

**Structure (Optimized for Recruiters & Professors):**
1. **Hero Header:** Project Name, Badges (CI Passing, Coverage 90%), high-quality screenshot of the Next.js UI.
2. **One-Sentence Pitch:** "A production-grade, zero-code RSS aggregation platform built with FastAPI and Next.js."
3. **Architecture Diagram:** Mermaid.js flowchart showing Scheduler → Normalizer → DB → FastAPI → Next.js.
4. **Core Features:** Emphasize "Circuit Breakers", "Idempotency", and "Advisory Locks".
5. **Quick Start:** 3 commands to run via Docker Compose.
6. **Technology Stack:** Clear list of tools and versions.

---

## PART 7 — FINAL OUTPUT

1. **Official v1.4.0 Scope:** Backend Stabilization + Next.js UI + CI/CD.
2. **Official v1.4.0 Architecture:** Headless FastAPI connected to Postgres, consumed by Next.js 15 App Router Server Components.
3. **Risks:** The database deduplication refactor (Task B) touches core ingestion logic and could temporarily break idempotency if the SQL `IN` clause misses hashes. Strict unit tests (Task E) mitigate this.
4. **Success Criteria:** 
   - A recruiter can visit a URL and immediately interact with the data.
   - The backend survives 2 concurrent Docker replicas without duplicate RSS fetching.
   - GitHub Actions shows green.

### FINAL VERDICT: GO 🟢

I approve the v1.4.0 implementation plan. We are ready to execute Week 1 (Backend Stabilization) immediately.
