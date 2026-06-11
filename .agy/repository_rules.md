# Repository Engineering Rules
**FOR AI AGENTS**

You are operating inside an operationally mature, high-throughput Financial News Aggregator. 

## Forbidden Architectural Patterns
1. **NO global state**. Do not use global mutable dictionaries.
2. **NO Celery / RabbitMQ / Redis**. The orchestration relies strictly on `APScheduler` embedded into the FastAPI `lifespan`. Do NOT recommend external task queues unless explicitly migrating off the embedded setup.
3. **NO raw SQL strings**. All DB access must use SQLAlchemy 2.0 executable constructs.
4. **NO offset pagination**. `OFFSET` is banned. All APIs must use keyset pagination via `(published_at, id)`.
5. **NO heavy ML libraries**. Do not import `spaCy`, `transformers`, or `nltk`. We rely on fast, deterministic Regex enrichment.

## Memory-Bound Processing Expectations
The `RSSCollector` parses XML dynamically. 
- You must chunk any bulk fetch operations.
- You must not eagerly load ORM relationships unless strictly required by the router (use `selectinload` over `joinedload` for 1:N).

## Core Directives
When generating code:
- Preserve `mypy` strict boundaries.
- Keep `ruff` completely silent.
- Enforce `async`/`await` correctly. Do not block the event loop.
