# Backend Architecture & Ingestion Pipeline Complete

> [!NOTE]
> The backend infrastructure and ingestion pipeline for the Indian Financial News Aggregator are now fully repaired, stabilized, and running with robust production boundaries.

## 1. Migration & Schema Stabilization
- **Fixed Corruption:** Completely deleted the corrupted Alembic history, dropped the existing Docker PostgreSQL volume, and generated a clean, deterministic baseline schema `21af7d79c2f7_initial_schema`.
- **Target Metadata Fix:** Updated `migrations/env.py` to import `app.models` so Alembic accurately detects all tables exported in `models/__init__.py`.
- **Validation:** Successfully ran `uv run alembic upgrade head` inside the clean container. All models are actively mapped.

## 2. Ingestion Pipeline & Boundaries (Orchestration)
Verified that the **Collector -> Processor -> Repository** boundaries strictly adhere to the defined architecture:
- **Collectors (`src/app/collectors`):** Handle raw HTTP/RSS fetching with deterministic retry strategies (`httpx` + `feedparser`). *No database awareness here.*
- **Processors (`src/app/processors`):** `ArticleNormalizer`, `QualityGate`, and hashing are completely stateless and pure Python data transformations.
- **Repositories (`src/app/db/repository.py`):** The `IngestionRepository.save_articles` method leverages PostgreSQL's native `ON CONFLICT DO NOTHING` via `index_elements=["url"]`. This pushes uniqueness deduplication entirely to the DB layer for atomicity.
- **Service Orchestration (`src/app/services/pipeline.py`):** Ties everything together seamlessly by calling Collectors concurrently, passing raw data through Processors, and sending normalized data to the Repository.

## 3. Scheduled Orchestration
- APScheduler is securely integrated in `src/app/orchestration/scheduler.py` with market-aware cron jobs (9-15 IST on weekdays, off-market on weekends).
- Wired elegantly into the FastAPI lifecycle in `src/app/core/startup.py`.

## 4. API & Export Layers
- **Read APIs (`src/app/api/routes/articles.py`):** Complete implementation of paginated listing (`CursorPage`) using PostgreSQL keyset pagination.
- **Full Text Search:** Supports native `ts_rank` using `websearch_to_tsquery` applied to the `search_vector` materialized index.
- **Data Export:** Streaming responses for CSV (`/articles/export/csv`) and Excel (`/articles/export/xlsx`) correctly pipe through chunks of the keyset pagination iterator.

## CI/CD Validations Passed
All CI tooling was executed against the modifications and returned clean:
```bash
uv run pytest -q                  # -> [100%] Pass
uv run ruff check src tests       # -> All checks passed!
uv run mypy src                   # -> Success: no issues found
```

> [!TIP]
> The backend is entirely stabilized and ready for frontend integration. You can start the server locally with: `uv run uvicorn app.main:app --app-dir src --reload`
