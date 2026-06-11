# Coding Principles

## Typing
- Everything must be typed.
- `mypy` must pass natively.

## N+1 Prevention
- Do NOT use SQLAlchemy `lazy="select"`.
- All relationships must be explicitly fetched using `selectinload()` within the Repository boundary if needed.
- APIs should map directly to scalar representations to avoid implicit lazy load crashes in an async context (`MissingGreenlet`).

## Naming
- Endpoints must be kebab-case (e.g., `/api/v1/feed-sources`).
- Python files are snake_case.
- Classes are PascalCase.

## Error Handling
- Never `except Exception: pass`.
- Wrap database errors in specific domain exceptions (`RepositoryError`) to decouple HTTP handlers from `sqlalchemy.exc` specifics.
