# Frontend-Backend Contract Audit

## Overview
This audit compares the API requests made by the Streamlit frontend against the FastAPI backend router definitions to identify the root causes of the observed UI widget failures.

## 1. Backend Endpoint Enumeration
The Streamlit frontend (`frontend/streamlit/app.py`) calls the following endpoints:
1. `GET {API_BASE_URL}/sources/`
2. `GET {API_BASE_URL}/pipeline/runs/?limit=10`
3. `GET {API_BASE_URL}/analytics/trending?time_window_hours=48`
4. `GET {API_BASE_URL}/articles/` (with query params)
5. `GET {API_BASE_URL}/articles/export/csv`

## 2. FastAPI Endpoint Verification
Based on the backend router definitions (`backend/src/app/api/routes/`):
- `sources.py`: `APIRouter(prefix="/sources")` with `@router.get("")` $\rightarrow$ Expects `/sources`
- `pipeline_runs.py`: `APIRouter(prefix="/pipeline-runs")` with `@router.get("")` $\rightarrow$ Expects `/pipeline-runs`
- `analytics.py`: `APIRouter(prefix="/analytics")` with `@router.get("/trending")` $\rightarrow$ Expects `/analytics/trending`
- `articles.py`: `APIRouter(prefix="/articles")` with `@router.get("")` $\rightarrow$ Expects `/articles`
- `articles.py`: `@router.get("/export/csv")` $\rightarrow$ Expects `/articles/export/csv`

---

## 3. Mismatch Matrix

| Frontend URL | Backend URL | Status | Root Cause |
| :--- | :--- | :--- | :--- |
| `/pipeline/runs/` | `/pipeline-runs` | **404 Not Found** | **Path Mismatch:** The frontend requests `/pipeline/runs/` while the FastAPI router is explicitly prefixed as `/pipeline-runs`. |
| `/sources/` | `/sources` | **307 Redirect** | **Trailing Slash Mismatch:** The frontend appends a trailing slash. FastAPI strictly matches `/sources` and issues a `307 Temporary Redirect` to strip the slash. The `httpx` client in the frontend does not follow redirects by default, resulting in a crash when attempting to parse the empty redirect body as JSON. |
| `/articles/` | `/articles` | **307 Redirect** | **Trailing Slash Mismatch:** Identical to `/sources/`. FastAPI expects `/articles` and redirects. `httpx` fails to follow the redirect. |

---

## 4. Widget Verification

| UI Component | Status | Cause of Failure | Required Fix |
| :--- | :--- | :--- | :--- |
| **Dashboard Page** | Partially Broken | Trending data loads, but pipeline/source widgets fail. | Fix underlying widget API calls. |
| **Pipeline Runs Widget** | **FAIL** | 404 from path mismatch. | Change frontend URL to `f"{API_BASE_URL}/pipeline-runs?limit=10"` |
| **Source Health Widget** | **FAIL** | 307 from trailing slash. | Change frontend URL to `f"{API_BASE_URL}/sources"` (remove slash). |
| **Article Explorer** | **FAIL** | 307 from trailing slash. | Change frontend URL to `f"{API_BASE_URL}/articles"` (remove slash). |
| **Search / Filters** | **FAIL** | 307 from trailing slash. | Same as Article Explorer. |
| **CSV Export** | **PASS** | URL strictly matches without a trailing slash (`/articles/export/csv`). | None required. |

## 5. Required Fixes (Summary)
To restore full functionality, the following lines in `frontend/streamlit/app.py` must be updated:
- **Line 38:** Change `httpx.get(f"{API_BASE_URL}/sources/")` to `httpx.get(f"{API_BASE_URL}/sources")`
- **Line 48:** Change `httpx.get(f"{API_BASE_URL}/pipeline/runs/?limit=10")` to `httpx.get(f"{API_BASE_URL}/pipeline-runs?limit=10")`
- **Line 135:** Change `httpx.get(f"{API_BASE_URL}/articles/", params=params)` to `httpx.get(f"{API_BASE_URL}/articles", params=params)`
