# Indian Financial News Aggregator — Backend Implementation Plan

Build out the full `collect → normalize → deduplicate → persist → export` pipeline across the existing skeleton.

## Current State

The project has a well-structured directory skeleton with dependencies declared in [pyproject.toml](file:///d:/indian-financial-news-aggregator/backend/pyproject.toml), a working Docker Compose setup, and a minimal FastAPI app in [main.py](file:///d:/indian-financial-news-aggregator/backend/src/app/main.py) with only a `/health` endpoint. **All module files are empty.**

## Proposed Changes

### Phase 1 — Core Infrastructure

Foundation that every other module depends on.

#### [MODIFY] [config.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/config.py)

Typed settings using `pydantic-settings`. Reads from env vars with sensible defaults.

```python
class Settings(BaseSettings):
    app_env: str          # development | staging | production
    log_level: str        # DEBUG | INFO | WARNING | ERROR
    
    # PostgreSQL
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    
    # Backend
    backend_host: str
    backend_port: int
    
    # Export
    export_dir: str
    
    # Optional API keys
    newsdata_api_key: str | None
    gnews_api_key: str | None

    @property
    def database_url(self) -> str:
        """Async postgres connection string."""
```

Exposes a `get_settings()` function cached with `@lru_cache`.

---

#### [MODIFY] [logging.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/logging.py)

Structlog configuration with JSON output in production, colored console output in development. Integrates with stdlib logging so SQLAlchemy / uvicorn logs are also captured.

---

#### [MODIFY] [exceptions.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/exceptions.py)

Domain exception hierarchy:

```
AppError (base)
├── CollectorError        — RSS/API fetch failures
├── NormalizationError    — article cleaning failures
├── DuplicateArticleError — dedup rejections (non-fatal)
├── ExportError           — file generation failures
└── NotFoundError         — entity lookups
```

Plus a FastAPI exception handler that maps these to HTTP responses with structured JSON bodies.

---

#### [MODIFY] [middleware.py](file:///d:/indian-financial-news-aggregator/backend/src/app/core/middleware.py)

- **RequestIdMiddleware** — generates a UUID per request, attaches it to structlog context and response headers.
- **RequestLoggingMiddleware** — logs method, path, status, and duration for every request.
- CORS middleware config (permissive for dev, locked down via env for prod).

---

### Phase 2 — Database Layer

#### [MODIFY] [base.py](file:///d:/indian-financial-news-aggregator/backend/src/app/db/base.py)

Declarative base with a `TimestampMixin` providing `created_at` / `updated_at` columns.

#### [MODIFY] [session.py](file:///d:/indian-financial-news-aggregator/backend/src/app/db/session.py)

Async engine and session factory using `asyncpg`. Exposes a `get_db()` async generator for FastAPI dependency injection.

#### [MODIFY] [models/__init__.py](file:///d:/indian-financial-news-aggregator/backend/src/app/models/__init__.py)

Re-exports all models for Alembic discovery.

#### [NEW] [article.py](file:///d:/indian-financial-news-aggregator/backend/src/app/models/article.py)

Core `Article` ORM model:

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | Server-default `gen_random_uuid()` |
| `title` | String(512) | Not null |
| `url` | String(2048) | Unique, not null |
| `source_feed` | String(256) | Which RSS feed/API it came from |
| `author` | String(256) | Nullable |
| `summary` | Text | Nullable, cleaned snippet |
| `content` | Text | Nullable, full text if available |
| `published_at` | DateTime(tz) | Nullable |
| `collected_at` | DateTime(tz) | Server default `now()` |
| `category` | String(128) | e.g. "Markets", "Economy" |
| `tags` | ARRAY(String) | Nullable |
| `content_hash` | String(64) | SHA-256 for dedup |
| `is_duplicate` | Boolean | Default False |

Indexes on `url` (unique), `content_hash`, `published_at`, `source_feed`.

#### [NEW] [feed_source.py](file:///d:/indian-financial-news-aggregator/backend/src/app/models/feed_source.py)

`FeedSource` model representing a configured RSS/API source:

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `name` | String(256) | e.g. "Economic Times - Markets" |
| `url` | String(2048) | Feed URL |
| `source_type` | String(32) | `rss` or `api` |
| `category` | String(128) | Default category for articles |
| `is_active` | Boolean | Enable/disable |
| `last_fetched_at` | DateTime(tz) | Nullable |

#### Alembic Setup

Initialize Alembic with async support and create an initial migration for both tables.

---

### Phase 3 — Schemas (Pydantic DTOs)

#### [MODIFY] [schemas/__init__.py](file:///d:/indian-financial-news-aggregator/backend/src/app/schemas/__init__.py)

Re-exports.

#### [NEW] [schemas/article.py](file:///d:/indian-financial-news-aggregator/backend/src/app/schemas/article.py)

- `ArticleCreate` — internal DTO from collectors
- `ArticleRead` — API response model
- `ArticleFilter` — query parameters (date range, source, category, search text)
- `PaginatedResponse[T]` — generic paginated wrapper

#### [NEW] [schemas/feed.py](file:///d:/indian-financial-news-aggregator/backend/src/app/schemas/feed.py)

- `FeedSourceCreate`, `FeedSourceRead`, `FeedSourceUpdate`

#### [NEW] [schemas/common.py](file:///d:/indian-financial-news-aggregator/backend/src/app/schemas/common.py)

- `HealthResponse`, `PipelineStatus`, `ExportRequest`

---

### Phase 4 — Collectors

#### [MODIFY] [collectors/__init__.py](file:///d:/indian-financial-news-aggregator/backend/src/app/collectors/__init__.py)

Define `BaseCollector` abstract class with `async def collect() -> list[ArticleCreate]`.

#### [NEW] [collectors/rss/parser.py](file:///d:/indian-financial-news-aggregator/backend/src/app/collectors/rss/parser.py)

`RSSCollector(BaseCollector)` — uses `httpx` to fetch + `feedparser` to parse. Handles:
- Concurrent fetching of multiple feeds
- Timeout / retry with `tenacity`
- Graceful error handling per-feed (one feed failure doesn't block others)
- Extracts title, url, summary, author, published date, categories

Preconfigured Indian financial news RSS feeds:

| Source | Feed URL |
|--------|----------|
| Economic Times - Markets | `https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms` |
| Economic Times - Economy | `https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms` |
| Moneycontrol - Markets | `https://www.moneycontrol.com/rss/marketreports.xml` |
| Moneycontrol - Business | `https://www.moneycontrol.com/rss/business.xml` |
| LiveMint - Markets | `https://www.livemint.com/rss/markets` |
| LiveMint - Economy | `https://www.livemint.com/rss/economy` |
| NDTV Profit | `https://feeds.feedburner.com/ndtvprofit-latest` |
| Business Standard | `https://www.business-standard.com/rss/markets-106.rss` |

#### [NEW] [collectors/apis/newsdata.py](file:///d:/indian-financial-news-aggregator/backend/src/app/collectors/apis/newsdata.py) (optional)

`NewsDataCollector(BaseCollector)` — calls NewsData.io API if `NEWSDATA_API_KEY` is set. Filters for Indian financial news. Skipped if no key configured.

---

### Phase 5 — Processors

#### [MODIFY] [processors/__init__.py](file:///d:/indian-financial-news-aggregator/backend/src/app/processors/__init__.py)

Re-exports.

#### [NEW] [processors/normalizer.py](file:///d:/indian-financial-news-aggregator/backend/src/app/processors/normalizer.py)

`ArticleNormalizer`:
- Strip HTML tags from summaries/content
- Normalize unicode and whitespace
- Parse and timezone-normalize dates to IST → UTC
- Clean/trim titles
- Generate `content_hash` (SHA-256 of normalized title + url)
- Validate required fields

#### [NEW] [processors/deduplicator.py](file:///d:/indian-financial-news-aggregator/backend/src/app/processors/deduplicator.py)

`ArticleDeduplicator`:
- **Exact dedup**: check `content_hash` against DB
- **URL dedup**: check `url` uniqueness
- **Fuzzy dedup**: use `rapidfuzz` to detect near-duplicate titles (configurable threshold, default 90%)
- Returns `(unique_articles, duplicate_count)` tuple

---

### Phase 6 — Services, Routes & Exporters

#### [MODIFY] [services/__init__.py](file:///d:/indian-financial-news-aggregator/backend/src/app/services/__init__.py)

Re-exports.

#### [NEW] [services/article_service.py](file:///d:/indian-financial-news-aggregator/backend/src/app/services/article_service.py)

Business logic layer — all DB access goes through here:
- `get_articles(filters, pagination)` — filtered, paginated queries
- `get_article_by_id(id)`
- `create_articles(articles: list[ArticleCreate])` — bulk insert with conflict handling
- `get_stats()` — article counts by source, date, category

#### [NEW] [services/pipeline_service.py](file:///d:/indian-financial-news-aggregator/backend/src/app/services/pipeline_service.py)

Orchestrates the full pipeline:
```
collect → normalize → deduplicate → persist
```
- Runs all active collectors concurrently
- Pipes raw articles through normalizer
- Deduplicates against existing DB content
- Bulk inserts unique articles
- Returns pipeline run summary (collected, normalized, duplicates, inserted)

#### [NEW] [services/feed_service.py](file:///d:/indian-financial-news-aggregator/backend/src/app/services/feed_service.py)

CRUD for feed sources.

---

#### [NEW] [api/routes/articles.py](file:///d:/indian-financial-news-aggregator/backend/src/app/api/routes/articles.py)

Thin routes, all logic delegated to services:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/articles` | List articles (filtered, paginated) |
| `GET` | `/api/v1/articles/{id}` | Get single article |
| `GET` | `/api/v1/articles/stats` | Aggregated statistics |

#### [NEW] [api/routes/feeds.py](file:///d:/indian-financial-news-aggregator/backend/src/app/api/routes/feeds.py)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/feeds` | List configured feeds |
| `POST` | `/api/v1/feeds` | Add new feed source |
| `PATCH` | `/api/v1/feeds/{id}` | Update feed |
| `DELETE` | `/api/v1/feeds/{id}` | Remove feed |

#### [NEW] [api/routes/pipeline.py](file:///d:/indian-financial-news-aggregator/backend/src/app/api/routes/pipeline.py)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/pipeline/run` | Trigger a pipeline run |
| `GET` | `/api/v1/pipeline/status` | Last run status |

#### [NEW] [api/routes/export.py](file:///d:/indian-financial-news-aggregator/backend/src/app/api/routes/export.py)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/export/csv` | Export filtered articles as CSV |
| `POST` | `/api/v1/export/excel` | Export filtered articles as Excel |

#### [MODIFY] [api/__init__.py](file:///d:/indian-financial-news-aggregator/backend/src/app/api/__init__.py)

Creates the v1 API router and includes all sub-routers.

---

#### [MODIFY] [exporters/__init__.py](file:///d:/indian-financial-news-aggregator/backend/src/app/exporters/__init__.py)

Re-exports.

#### [NEW] [exporters/csv_exporter.py](file:///d:/indian-financial-news-aggregator/backend/src/app/exporters/csv_exporter.py)

Generates CSV from article data using `pandas`. Streams to `BytesIO` for download.

#### [NEW] [exporters/excel_exporter.py](file:///d:/indian-financial-news-aggregator/backend/src/app/exporters/excel_exporter.py)

Generates `.xlsx` with `openpyxl` via pandas. Includes formatting (header styles, auto-width columns).

---

#### [MODIFY] [main.py](file:///d:/indian-financial-news-aggregator/backend/src/app/main.py)

Wire everything together:
- Configure structlog on import
- Create `FastAPI` with lifespan handler (init DB engine, seed default feeds, shutdown cleanup)
- Mount middleware
- Include API router
- Register exception handlers

---

### Phase 7 — Alembic + Seed Data

#### [NEW] [alembic.ini](file:///d:/indian-financial-news-aggregator/backend/alembic.ini) + [migrations/](file:///d:/indian-financial-news-aggregator/backend/migrations/)

Standard Alembic async setup pointing at the same `database_url` from settings.

#### [NEW] [scripts/seed_feeds.py](file:///d:/indian-financial-news-aggregator/backend/scripts/seed_feeds.py)

Script to seed the 8 preconfigured Indian financial news feeds into the `feed_sources` table.

---

## Open Questions

> [!IMPORTANT]
> **Feed source management**: Should the 8 default Indian news feeds be auto-seeded into the database on first startup (via lifespan handler), or kept as a separate seed script to run manually?

> [!IMPORTANT]
> **Scheduled collection**: The plan currently has pipeline runs triggered via `POST /api/v1/pipeline/run` (manual trigger). Do you want a built-in scheduler (e.g., APScheduler or a simple background task loop) to automatically collect news on an interval, or is manual/cron-based triggering sufficient for now?

> [!IMPORTANT]
> **Alembic in this phase**: Do you want me to fully set up Alembic with async support and generate the initial migration, or would you prefer to defer migrations and use `create_all()` for now during development?

## Verification Plan

### Automated Tests
```bash
# After implementation, from backend/:
uv run pytest tests/ -v
```

### Manual Verification
1. Start the stack: `docker compose up --build`
2. Verify health: `GET /health` → `{"status": "ok"}`
3. Trigger pipeline: `POST /api/v1/pipeline/run` → returns run summary
4. List articles: `GET /api/v1/articles` → paginated article list
5. Export: `POST /api/v1/export/csv` → downloadable CSV
6. Check structured logs in container output
