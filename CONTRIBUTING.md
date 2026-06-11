# Contributing Guidelines

This repository maintains elite systems engineering standards. All contributions must adhere strictly to these rules.

## Core Philosophy
We optimize for:
1. Operational deterministic behavior.
2. Memory safety over syntactic brevity.
3. Observability and traceability.
4. Zero-downtime database interactions.

## Coding Standards
- **Typing**: Strict `mypy` enforcement. All functions, signatures, and variables must be fully typed. No implicit `Any`.
- **Linting**: `ruff` is the absolute authority on style. No exceptions.
- **Async Execution**: `await` boundaries must be respected. Never perform blocking I/O (e.g., `requests`, `time.sleep`) within the async event loop.
- **SQLAlchemy 2.0**: All queries must use the 2.0 executable syntax (`select()`, `insert()`). No legacy `Query` usage.
- **Exception Handling**: Catch specific exceptions. Never bare `except:`. Domain layers must wrap infrastructure exceptions into domain concepts (`RepositoryError`, etc.).

## Validation Workflow
Before submitting any pull request or committing changes:
```bash
uv run ruff check .
uv run mypy .
uv run pytest
```
If ANY of these fail, the code is fundamentally un-mergable.

## Database Migration Workflow
- Use `uv run alembic revision --autogenerate -m "description"`
- **NEVER** modify existing migration files once merged to `main`.
- **ALWAYS** check downgrades. Ensure PostgreSQL enum casts or custom types are explicitly managed in downgrade methods (e.g., `postgresql_using`).

## Commit Conventions
We use conventional commits:
- `feat:` new capabilities
- `fix:` bug resolution
- `refactor:` code restructuring without behavioral change
- `docs:` documentation only
- `test:` test files
- `chore:` maintenance and dependency updates

## Branching Conventions
- `main` is sacred and deployable at all times.
- Feature branches must follow: `feat/issue-123-short-description`
- Bugfix branches must follow: `fix/issue-456-bug-description`

## Testing Expectations
- All new API routes require an integration test via FastAPI `TestClient`.
- All DB repositories require tests verifying `ON CONFLICT` constraints and transaction isolation.
- All ingestion parsing requires chaotic edge-case tests (malformed XML, missing tags, timezone shifts).
