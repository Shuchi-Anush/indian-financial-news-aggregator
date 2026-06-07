# Engineering Principles

## 1. Maintainability Over Cleverness

Write code that a new contributor understands in 60 seconds. Explicit is better than implicit. If a pattern requires a comment explaining why it exists, it might be too clever.

## 2. Async-First, Sync-Never

Every I/O operation (DB, HTTP, file) must be async. Use `httpx.AsyncClient`, `sqlalchemy.ext.asyncio`, `aiofiles`. Never block the event loop with synchronous calls.

## 3. Thin Routes, Fat Services

API route handlers validate input (via Pydantic) and return output. All business logic lives in `services/`. Routes are glue — 5-15 lines max.

## 4. Explicit Dependencies

Use FastAPI's `Depends()` for DB sessions, settings, and services. No module-level singletons. No hidden global state. Every function declares what it needs.

## 5. Fail Loudly, Recover Gracefully

- Log every error with structured context (structlog)
- Use domain exceptions, not bare `raise Exception`
- One failing RSS feed must not crash the entire pipeline run
- Return partial results with error metadata, not 500s

## 6. Type Everything

- All function signatures fully typed (params + return)
- Pydantic models for all data boundaries (API, DB, inter-module)
- `mypy --strict` compatibility as a goal

## 7. Test at Boundaries

Focus tests on service-level behavior and integration points, not internal implementation details. Mock external HTTP calls, never mock the ORM.

## 8. Incremental Delivery

Build vertically (one complete feature end-to-end) before building horizontally. A working RSS collector with one feed is better than a half-built framework for ten sources.

## 9. No Premature Abstraction

Don't build a "plugin system" until you have 3+ concrete plugins. Don't add a message queue until sync processing is provably insufficient. The second implementation reveals the right abstraction.

## 10. Production-Oriented Defaults

- Structured JSON logs in production
- Request correlation IDs on every request
- Health check endpoints from day one
- Docker-first deployment model
- Environment-based configuration (never hardcode)
