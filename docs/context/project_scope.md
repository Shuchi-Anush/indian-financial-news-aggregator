# Project Scope

## What This Project Is

A modular backend system that:
1. **Collects** Indian financial news from RSS feeds and optional APIs
2. **Normalizes** raw article data (HTML stripping, date parsing, unicode cleanup)
3. **Deduplicates** articles using URL matching, content hashing, and fuzzy title comparison
4. **Persists** structured article data in PostgreSQL
5. **Exports** articles via REST API and CSV/Excel file downloads

## Target Audience

- Academic demonstration of production-quality backend engineering
- Professor/student evaluation of clean architecture, modularity, and engineering practices
- Portfolio showcase for async Python backend design

## Scale Assumptions

| Metric | Expected Range |
|--------|---------------|
| RSS feed sources | 8–15 |
| New articles per day | 200–500 |
| Total stored articles | 10K–100K over months |
| Concurrent API users | 1–5 (demo/dev) |
| Pipeline runs per day | 1–48 (manual or cron) |
| Export file size | <10MB typical |

## Current Phase: Backend Infrastructure

Focus is exclusively on:
- Core infrastructure (config, logging, exceptions, middleware)
- Database layer (models, session management)
- Ingestion pipeline (collectors, normalizer, deduplicator)
- REST API (articles, feeds, pipeline trigger, export)
- Docker-based deployment

## What's Next (Future Phases)

1. Streamlit dashboard for basic visualization
2. Additional API collectors (NewsData.io, GNews)
3. Article search (PostgreSQL full-text search)
4. Pipeline run history and statistics
5. Alembic migrations (when schema stabilizes)
6. GitHub Actions CI (lint + test)
