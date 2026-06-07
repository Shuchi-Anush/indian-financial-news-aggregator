# Current Priorities

## P0 — Must Have (this sprint)

1. **Core infrastructure** — config, logging, exceptions, middleware. Everything else depends on this.
2. **Database layer** — models + session. Can't persist or deduplicate without storage.
3. **RSS collector** — at least one working feed. This is the core input.
4. **Normalizer + deduplicator** — the pipeline's value proposition.
5. **Pipeline service** — end-to-end `collect → normalize → deduplicate → persist`.
6. **Article listing API** — prove the pipeline works by querying results.

## P1 — Should Have (this sprint if time permits)

7. **Feed source CRUD API** — manage feeds via API instead of direct DB edits.
8. **CSV/Excel export** — the export leg of the pipeline.
9. **Seed script** — populate default feeds without manual SQL.

## P2 — Nice to Have (next sprint)

10. **Pipeline status/history** — track past runs with timing and counts.
11. **Article search** — full-text search within stored articles.
12. **Streamlit dashboard** — basic visualization frontend.

## Not Now

- Authentication / user management
- Rate limiting
- Background scheduler (use cron or manual triggers)
- Additional API sources (NewsData.io, GNews)
- Sentiment analysis / NLP
- Frontend (web/mobile)
