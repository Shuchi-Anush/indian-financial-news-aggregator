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
from fastapi.responses import Response  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.api.routes import admin, analytics, articles, pipeline_runs, sources  # noqa: E402
from app.core.exceptions import register_exception_handlers  # noqa: E402
from app.core.middleware import register_middleware  # noqa: E402
from app.core.startup import lifespan  # noqa: E402
from app.db.session import get_engine  # noqa: E402

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


@app.get("/health", tags=["system"], include_in_schema=False)
async def health_check_legacy() -> dict[str, str]:
    """Legacy health check. Deprecated in favor of /health/live and /health/ready."""
    return {"status": "ok"}


@app.get("/health/live", tags=["system"])
async def health_live() -> dict[str, str]:
    """Liveness probe — returns 200 if the process is running."""
    return {"status": "ok", "service": "financial-news-backend"}


@app.get("/health/ready", tags=["system"])
async def health_ready() -> dict[str, str]:
    """Readiness probe — verifies PostgreSQL connectivity."""
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.get("/metrics", tags=["system"])
async def metrics_endpoint() -> Response:
    """Expose Prometheus-compatible operational metrics."""
    from app.core.metrics import export_metrics

    data, content_type = await export_metrics()
    return Response(content=data, media_type=content_type)

