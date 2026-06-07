# Architecture Rules

Hard constraints. Violating these requires an ADR (docs/decisions/).

## Layer Boundaries

1. **Routes MUST NOT import from `models/` or `db/`** — routes interact with the database only through services.
2. **Routes MUST NOT contain business logic** — validation, filtering, transformation, and persistence belong in services or processors.
3. **Services own all database access** — `get_db()` is injected into services, never into route handlers directly.
4. **Collectors MUST NOT write to the database** — they return `list[ArticleCreate]` schemas. Persistence is the pipeline service's job.
5. **Processors are stateless** — normalizer and deduplicator receive data in, return data out. No side effects.

## Dependency Direction

```
routes → services → {processors, collectors, exporters, db}
```

No circular imports. No reverse dependencies. If module A imports module B, module B must never import module A.

## Data Contracts

6. **All API boundaries use Pydantic schemas** — never expose ORM models in route responses.
7. **Internal data transfer uses typed schemas** — collectors produce `ArticleCreate`, services consume them.
8. **Database models stay in `models/`** — one file per table, re-exported from `models/__init__.py`.

## Configuration

9. **No hardcoded connection strings, API keys, or secrets** — everything via `Settings` from `core/config.py`.
10. **No mutable global state** — settings are read-only after startup.

## Error Handling

11. **Domain exceptions only** — use the hierarchy in `core/exceptions.py`. Never raise `ValueError` or `RuntimeError` from business logic.
12. **One failing source must not break the pipeline** — collector errors are logged and skipped, not propagated.

## Scope Boundaries

13. **No Kubernetes, no microservices, no event buses** — single-process FastAPI monolith deployed via Docker Compose.
14. **No premature AI/ML integration** — sentiment analysis, NER, etc. are future phases. Don't scaffold for them now.
15. **Backend-first** — frontend work does not drive backend API design changes.
