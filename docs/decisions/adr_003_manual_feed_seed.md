# ADR-003: Manual Feed Seeding via Script

**Status:** Accepted  
**Date:** 2026-06-07  
**Context:** How to populate the default Indian financial news RSS feeds into the database.

## Decision

Default feed sources are loaded via a standalone seed script (`scripts/seed_feeds.py`), run manually after the database is initialized. Not auto-seeded on application startup.

## Rationale

- Startup should be fast and predictable — no DB writes on every boot
- Seed data is a one-time operation, not a per-restart operation
- Script-based seeding is idempotent (upsert on URL) and explicit
- Avoids race conditions if multiple instances start simultaneously (future)
- Operators can customize feeds before running the seed

## Consequences

- After first `docker compose up`, the `feed_sources` table is empty until the seed script runs
- Pipeline will collect nothing until feeds are seeded
- Documentation must clearly state: "run seed script after first startup"

## Seed Script Behavior

```python
# scripts/seed_feeds.py
# - Reads default feed list from a constant
# - Connects to PostgreSQL
# - Upserts each feed (INSERT ON CONFLICT DO NOTHING on url)
# - Logs count of inserted/skipped feeds
```
