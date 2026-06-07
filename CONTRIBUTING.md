# Contributing

## Development Setup

See [docs/operations/local_development.md](docs/operations/local_development.md) for full setup instructions.

## Code Standards

- **Linter/Formatter:** `ruff` (configured in `pyproject.toml`)
- **Type checker:** `mypy`
- **Test framework:** `pytest` with `pytest-asyncio`
- **Full standards:** See [.claude/coding_standards.md](.claude/coding_standards.md)

## Before Submitting Changes

```bash
cd backend

# Format
uv run ruff format src/

# Lint
uv run ruff check src/ --fix

# Type check
uv run mypy src/app/

# Test
uv run pytest tests/ -v
```

## Architecture Rules

Read [.claude/architecture_rules.md](.claude/architecture_rules.md) before making structural changes. Key rules:

1. No business logic in route handlers
2. No direct DB access from routes
3. Collectors return DTOs, never write to DB
4. All API boundaries use Pydantic schemas
5. Domain exceptions only (from `core/exceptions.py`)

## Adding a New RSS Feed Source

1. Add the feed to `scripts/seed_feeds.py`
2. Run the seed script
3. Test with `POST /api/v1/pipeline/run`
4. Document any source-specific quirks in [docs/architecture/collector_strategy.md](docs/architecture/collector_strategy.md)

## Adding a New API Endpoint

1. Create route module in `api/routes/`
2. Create corresponding service in `services/`
3. Register router in `api/__init__.py`
4. Add to [docs/api/api_contracts.md](docs/api/api_contracts.md)
5. Follow the template in [.agy/templates/api_route_template.md](.agy/templates/api_route_template.md)

## Architecture Decisions

If your change affects architecture (new dependencies, layer boundary changes, new infrastructure), write an ADR in `docs/decisions/` following the existing format.
