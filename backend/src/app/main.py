"""Application entry point — composition root.

Initializes logging, creates the FastAPI app, and wires together
middleware, exception handlers, and the lifespan manager.

Run with::

    uv run uvicorn app.main:app --app-dir src --reload
"""

from app.core.env_loader import load_environment

load_environment()

from app.core.logging import setup_logging  # noqa: E402

# Configure structured logging before anything else
setup_logging()

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import PlainTextResponse  # noqa: E402

from app.api.routes import admin, analytics, articles, pipeline_runs, sources  # noqa: E402
from app.core.exceptions import register_exception_handlers  # noqa: E402
from app.core.middleware import register_middleware  # noqa: E402
from app.core.startup import lifespan  # noqa: E402

app = FastAPI(
    title="Indian Financial News Aggregator",
    version="0.1.0",
    description="Collects, normalizes, deduplicates, and serves Indian financial news.",
    lifespan=lifespan,
)

# Wire middleware (request ID, logging, CORS)
register_middleware(app)

# Wire exception handlers (domain errors → JSON responses)
register_exception_handlers(app)

# Register routers
app.include_router(articles.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(sources.router)
app.include_router(pipeline_runs.router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Liveness probe — returns 200 if the process is running."""
    return {"status": "ok"}


@app.get("/metrics", tags=["system"])
async def metrics_endpoint() -> PlainTextResponse:
    """Expose Prometheus-compatible operational metrics."""
    from app.core.metrics import export_metrics

    return PlainTextResponse(await export_metrics())
