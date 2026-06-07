# Active Sprint

## Sprint: Backend Core Infrastructure

**Goal:** Implement the full `collect → normalize → deduplicate → persist → export` pipeline.

**Status:** Not started — documentation layer just completed.

### Sprint Backlog

#### 1. Core Infrastructure (`core/`)
- [ ] `config.py` — Settings via pydantic-settings
- [ ] `logging.py` — Structlog configuration
- [ ] `exceptions.py` — Domain exception hierarchy + FastAPI handlers
- [ ] `middleware.py` — Request ID, request logging, CORS

#### 2. Database Layer (`db/` + `models/`)
- [ ] `db/base.py` — Declarative base with TimestampMixin
- [ ] `db/session.py` — Async engine, session factory, get_db()
- [ ] `models/article.py` — Article ORM model
- [ ] `models/feed_source.py` — FeedSource ORM model
- [ ] Table creation via `create_all()` in lifespan

#### 3. Schemas (`schemas/`)
- [ ] `schemas/article.py` — ArticleCreate, ArticleRead, ArticleFilter, PaginatedResponse
- [ ] `schemas/feed.py` — FeedSourceCreate, FeedSourceRead, FeedSourceUpdate
- [ ] `schemas/common.py` — HealthResponse, PipelineRunResult

#### 4. Collectors (`collectors/`)
- [ ] `collectors/__init__.py` — BaseCollector ABC
- [ ] `collectors/rss/parser.py` — RSSCollector with 8 Indian feeds

#### 5. Processors (`processors/`)
- [ ] `processors/normalizer.py` — HTML strip, unicode, date parsing, hash generation
- [ ] `processors/deduplicator.py` — URL, hash, and fuzzy title dedup

#### 6. Services (`services/`)
- [ ] `services/article_service.py` — CRUD + filtered queries
- [ ] `services/pipeline_service.py` — Full pipeline orchestration
- [ ] `services/feed_service.py` — Feed source CRUD

#### 7. API Routes (`api/routes/`)
- [ ] `api/__init__.py` — v1 router assembly
- [ ] `api/routes/articles.py` — Article listing, detail, stats
- [ ] `api/routes/feeds.py` — Feed source CRUD endpoints
- [ ] `api/routes/pipeline.py` — Pipeline trigger
- [ ] `api/routes/export.py` — CSV/Excel export

#### 8. Exporters (`exporters/`)
- [ ] `exporters/csv_exporter.py`
- [ ] `exporters/excel_exporter.py`

#### 9. Wiring (`main.py`)
- [ ] Lifespan handler (DB init, shutdown)
- [ ] Middleware registration
- [ ] Router mounting
- [ ] Exception handler registration

#### 10. Seed Script
- [ ] `scripts/seed_feeds.py` — Populate default Indian financial news feeds

### Implementation Order

```
core/ → db/ → models/ → schemas/ → collectors/ → processors/ → services/ → api/ → exporters/ → main.py → seed script
```

Dependencies flow left-to-right. Each layer can be tested independently before wiring the next.
