# Implementation Prompt

Use this prompt when asking an AI assistant to implement a new feature or module.

---

You are implementing a feature for the Indian Financial News Aggregator backend.

**Before writing any code:**
1. Read `.claude/repository_map.md` for project structure
2. Read `.claude/architecture_rules.md` for hard constraints
3. Read `.claude/coding_standards.md` for style patterns
4. Read `.claude/backend_conventions.md` for route/service/collector templates

**Implementation rules:**
- Use async for all I/O (httpx, SQLAlchemy async, aiofiles)
- Use Pydantic v2 syntax (ConfigDict, not class Config)
- Use SQLAlchemy 2.0 style (Mapped[], mapped_column())
- Use structlog for logging with structured key-value pairs
- Keep route handlers under 15 lines — delegate to services
- All functions must have full type annotations
- Domain exceptions only (from core/exceptions.py)
- One failing component must not crash the system

**Feature to implement:**
[Describe the specific feature here]

**Files to create or modify:**
[List the specific files]

**Acceptance criteria:**
[List what "done" looks like]
