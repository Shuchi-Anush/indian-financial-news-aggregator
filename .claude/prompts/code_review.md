# Code Review Prompt

Use this prompt when asking an AI assistant to review code changes.

---

Review the following code changes for the Indian Financial News Aggregator backend.

**Check against these standards:**

1. **Architecture rules** (`.claude/architecture_rules.md`):
   - Are layer boundaries respected? (routes → services → db)
   - Do routes contain business logic? (they shouldn't)
   - Do collectors write to the database? (they shouldn't)

2. **Coding standards** (`.claude/coding_standards.md`):
   - Full type annotations on all functions?
   - Async for all I/O?
   - Structlog with structured context (not f-strings)?
   - Domain exceptions (not bare Exception)?
   - Pydantic v2 syntax?
   - SQLAlchemy 2.0 mapped_column style?

3. **Error handling**:
   - Will one failing RSS feed crash the pipeline?
   - Are errors logged with sufficient context for debugging?
   - Are HTTP errors returned as structured JSON?

4. **Production readiness**:
   - Are there any hardcoded values that should be in config?
   - Is there any synchronous I/O blocking the event loop?
   - Are database queries efficient (N+1, missing indexes)?

**Code to review:**
[Paste code or file paths here]
