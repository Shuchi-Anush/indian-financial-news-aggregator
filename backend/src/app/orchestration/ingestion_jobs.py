import asyncio

import structlog

# Import our collectors
from app.collectors.rss.businessstandard import BusinessStandardRSSCollector
from app.collectors.rss.cnbctv18 import CNBCTV18RSSCollector
from app.collectors.rss.economictimes import EconomicTimesRSSCollector
from app.collectors.rss.livemint import LiveMintRSSCollector
from app.collectors.rss.moneycontrol import MoneycontrolRSSCollector
from app.collectors.rss.sebi import SebiRSSCollector
from app.db.repository import IngestionRepository
from app.db.session import get_session_factory
from app.domain.collectors import SourceMetadata
from app.models.feed_source import CircuitBreakerState
from app.services.pipeline import IngestionPipeline

log = structlog.get_logger()

# Async process-safe lock to prevent overlapping runs
_ingestion_lock = asyncio.Lock()
# Track active ingestion task for graceful cancellation
_active_ingestion_task: asyncio.Task | None = None


def _instantiate_collector(source_dict: dict):
    slug = source_dict["slug"]
    meta = SourceMetadata(
        source_id=source_dict["id"],
        name=source_dict["name"],
        url=source_dict["url"],
        source_type=source_dict["source_type"].value,
        timezone_hint=source_dict["timezone_hint"],
    )
    if slug == "business-standard-markets":
        return BusinessStandardRSSCollector(meta)
    elif slug == "cnbc-tv18-markets":
        return CNBCTV18RSSCollector(meta)
    elif slug == "economic-times-markets":
        return EconomicTimesRSSCollector(meta)
    elif slug == "livemint-markets":
        return LiveMintRSSCollector(meta)
    elif slug == "moneycontrol-markets":
        return MoneycontrolRSSCollector(meta)
    elif slug == "sebi-press-releases":
        return SebiRSSCollector(meta)
    return None


async def _run_pipeline():
    session_factory = get_session_factory()
    if not session_factory:
        log.error("session_factory_not_initialized")
        return

    repo = IngestionRepository(session_factory)
    try:
        active_sources = await repo.get_active_sources()

        collectors = []
        for s in active_sources:
            if s["circuit_breaker_state"] == CircuitBreakerState.OPEN:
                log.warning("source_skipped_circuit_open", slug=s["slug"])
                continue

            collector = _instantiate_collector(s)
            if collector:
                collectors.append(collector)

        if not collectors:
            log.info("no_collectors_active")
            return

        pipeline = IngestionPipeline(repo)
        await pipeline.run(collectors)
    except asyncio.CancelledError:
        log.warning("ingestion_cycle_cancelled_gracefully")
        raise
    except Exception as e:
        log.exception("ingestion_cycle_crash", error=str(e))


async def run_ingestion_cycle():
    """Triggered by the scheduler to run an ingestion pipeline cycle safely."""
    global _active_ingestion_task

    if _ingestion_lock.locked():
        log.warning("ingestion_cycle_skipped_due_to_lock")
        return

    async with _ingestion_lock:
        log.info("ingestion_cycle_started")
        _active_ingestion_task = asyncio.current_task()
        try:
            await _run_pipeline()
        finally:
            _active_ingestion_task = None


async def graceful_shutdown(timeout_seconds: float = 15.0):
    """Wait for the active ingestion cycle to complete, or cancel it if it times out."""
    if _ingestion_lock.locked() and _active_ingestion_task and not _active_ingestion_task.done():
        log.info("waiting_for_active_ingestion_cycle_to_finish", timeout_seconds=timeout_seconds)
        try:
            # We want to wait for the task to finish without cancelling it immediately.
            # But wait_for will cancel the awaitable if it times out. Since we are awaiting an existing task,
            # wait_for will cancel the task.
            await asyncio.wait_for(asyncio.shield(_active_ingestion_task), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            log.warning("ingestion_cycle_shutdown_timeout_exceeded_cancelling")
            if not _active_ingestion_task.done():
                _active_ingestion_task.cancel()
                try:
                    # Give it a tiny bit of time to handle the CancelledError
                    await asyncio.wait([_active_ingestion_task], timeout=2.0)
                except Exception:
                    pass
    log.info("ingestion_jobs_shutdown_complete")
