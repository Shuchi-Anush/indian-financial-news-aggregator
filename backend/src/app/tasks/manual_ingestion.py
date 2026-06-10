"""Manual ingestion trigger for local development and testing."""

import asyncio
import uuid

import structlog

from app.collectors.rss.moneycontrol import MoneycontrolRSSCollector
from app.core.logging import setup_logging
from app.db.repository import IngestionRepository
from app.db.session import initialize_database, dispose_engine, get_session_factory
from app.domain.collectors import SourceMetadata
from app.services.pipeline import IngestionPipeline

log = structlog.get_logger()


async def main():
    """Execute a single end-to-end ingestion run for the Moneycontrol feed."""
    setup_logging()
    log.info("manual_ingestion_starting")

    log.info("initializing_database")
    await initialize_database()
    log.info("database_initialized")

    # Setup repository and pipeline
    repository = IngestionRepository(get_session_factory())
    pipeline = IngestionPipeline(repository)

    url = "https://www.moneycontrol.com/rss/MCtopnews.xml"
    feed_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))

    metadata = SourceMetadata(
        source_id=feed_id,
        name="Moneycontrol Markets",
        url=url,
        source_type="rss",
        timezone_hint="Asia/Kolkata",
    )

    collector = MoneycontrolRSSCollector(metadata)

    summary = await pipeline.run([collector])

    print("\n" + "=" * 30)
    print(" INGESTION SUMMARY")
    print("=" * 30)
    print(f"Status:     {summary.status.value}")
    print(f"Inserted:   {summary.inserted_count}")
    print(f"Duplicates: {summary.duplicate_count}")
    print(f"Errors:     {len(summary.errors)}")
    for err in summary.errors:
        print(f" - {err}")
    print("=" * 30 + "\n")

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
