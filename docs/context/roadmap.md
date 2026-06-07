# Roadmap

## Phase 1: Backend Core (Current)

**Goal:** Working `collect → normalize → deduplicate → persist → export` pipeline.

| Component | Status |
|-----------|--------|
| Project skeleton + dependencies | ✅ Done |
| Docker Compose (PostgreSQL + backend) | ✅ Done |
| Documentation governance layer | ✅ Done |
| Core infrastructure (config, logging, exceptions, middleware) | ⬜ Not started |
| Database layer (models, session, create_all) | ⬜ Not started |
| Pydantic schemas (DTOs) | ⬜ Not started |
| RSS collector (8 Indian financial feeds) | ⬜ Not started |
| Normalizer + Deduplicator | ⬜ Not started |
| Pipeline service (orchestration) | ⬜ Not started |
| REST API (articles, feeds, pipeline, export) | ⬜ Not started |
| CSV/Excel exporters | ⬜ Not started |
| Feed seed script | ⬜ Not started |

**Exit criteria:** `POST /api/v1/pipeline/run` collects articles from live RSS feeds, deduplicates them, stores in PostgreSQL, and articles are retrievable via `GET /api/v1/articles` and exportable as CSV/Excel.

---

## Phase 2: Polish + Observability

- Pipeline run history (persist run results to DB)
- Article statistics endpoint (counts by source, category, date)
- Alembic migration setup
- Improved error reporting in API responses
- GitHub Actions CI (ruff + pytest on PR)
- Additional RSS feeds based on Phase 1 experience

---

## Phase 3: Visualization + API Sources

- Streamlit dashboard (article browser, pipeline status, source stats)
- NewsData.io collector (optional, API key required)
- GNews collector (optional, API key required)
- PostgreSQL full-text search on articles

---

## Phase 4: Frontend + Extended Features

- Next.js web frontend (article browser, search, export)
- Article tagging / categorization improvements
- Pagination performance optimization
- Export scheduling (periodic CSV generation)

---

## Not Planned

See [non_goals.md](non_goals.md) for things explicitly excluded from the roadmap.
