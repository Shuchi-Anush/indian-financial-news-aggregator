import asyncio
import sys

# Bootstrap environment before any app imports
from app.core.env_loader import load_environment
load_environment()

from app.core.logging import setup_logging
setup_logging()

import structlog
from app.db.session import initialize_database, get_session_factory, dispose_engine
from app.db.repository import IngestionRepository
from app.orchestration.ingestion_jobs import _instantiate_collector
from app.services.pipeline import IngestionPipeline
from app.models.feed_source import CircuitBreakerState

log = structlog.get_logger()

async def main():
    log.info("manual_ingestion_starting")
    
    # 1. Initialize database
    await initialize_database()
    session_factory = get_session_factory()
    repo = IngestionRepository(session_factory)
    
    # 2. Fetch active sources
    active_sources = await repo.get_active_sources()
    log.info("active_sources_found", count=len(active_sources))
    
    if not active_sources:
        log.error("NO_SOURCES_FOUND")
        await dispose_engine()
        sys.exit(1)
    
    # 3. Instantiate collectors
    collectors = []
    for s in active_sources:
        if s["circuit_breaker_state"] == CircuitBreakerState.OPEN:
            log.warning("source_skipped_circuit_open", slug=s["slug"])
            continue
        collector = _instantiate_collector(s)
        if collector:
            collectors.append(collector)
        else:
            log.warning("no_collector_for_slug", slug=s["slug"])
    
    log.info("collectors_instantiated", count=len(collectors))
    
    if not collectors:
        log.error("NO_COLLECTORS")
        await dispose_engine()
        sys.exit(1)
    
    # 4. Run pipeline
    pipeline = IngestionPipeline(repo)
    result = await pipeline.run(collectors)
    
    log.info(
        "pipeline_result",
        status=result.status.value,
        articles_ingested=result.articles_ingested,
        duplicates_detected=result.duplicates_detected,
        failures=result.failures,
        duration_ms=result.duration_ms,
        error_summary=result.error_summary,
    )
    
    await dispose_engine()
    log.info("manual_ingestion_complete")

if __name__ == "__main__":
    asyncio.run(main())
