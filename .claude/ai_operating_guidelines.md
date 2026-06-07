# AI Operating Guidelines

## Context

This is a production-minded Indian Financial News Aggregator. It is a professor-demo-grade system — robust enough for a real demo, clean enough to showcase engineering quality, pragmatic enough to ship.

## Before Writing Code

1. **Read `repository_map.md`** — understand where things live
2. **Read `architecture_rules.md`** — understand hard constraints
3. **Read `coding_standards.md`** — match existing patterns
4. **Check `docs/decisions/`** — respect settled ADRs

## When Generating Code

- Follow the existing module structure exactly — don't reorganize
- Match the import style, naming, and patterns in `backend_conventions.md`
- Use async everywhere for I/O operations
- Use `structlog` for logging, never `print()` or stdlib `logging` directly
- Use Pydantic v2 syntax (`model_config = ConfigDict(...)`, not `class Config`)
- Use SQLAlchemy 2.0 style (`Mapped[]`, `mapped_column()`, not `Column()`)
- Keep route handlers under 15 lines
- Always include type annotations on all function signatures

## What NOT To Do

- Don't add Kubernetes, Helm, or cloud-provider-specific infrastructure
- Don't add microservice patterns (message queues, service mesh, gRPC)
- Don't add ML/AI features (sentiment analysis, NER, embeddings)
- Don't add caching layers (Redis) unless explicitly asked
- Don't add authentication/authorization unless explicitly asked
- Don't scaffold for features that aren't in the current sprint
- Don't create abstract base classes until there are 2+ concrete implementations
- Don't add `# TODO` comments as a substitute for actual implementation
- Don't generate placeholder files with only docstrings or pass statements

## When Uncertain

- Ask before adding new dependencies to `pyproject.toml`
- Ask before creating new top-level directories
- Ask before changing the database schema design
- Prefer the simpler approach — complexity can be added later

## File Modification Rules

- When modifying existing files, preserve all unrelated comments and code
- When creating new modules, include a module-level docstring explaining purpose
- When adding new models, update `models/__init__.py` re-exports
- When adding new routes, register them in `api/__init__.py`
