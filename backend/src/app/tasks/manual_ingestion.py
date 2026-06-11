"""Manual ingestion trigger for local development and testing."""
# ruff: noqa: E402

import asyncio
import sys
import uuid
from pathlib import Path

# Fix import path for standalone script execution
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.core.env_loader import load_environment

load_environment()

import structlog

from app.collectors.rss.businessstandard import BusinessStandardRSSCollector
from app.collectors.rss.cnbctv18 import CNBCTV18RSSCollector
from app.collectors.rss.economictimes import EconomicTimesRSSCollector
from app.collectors.rss.livemint import LiveMintRSSCollector
from app.collectors.rss.moneycontrol import MoneycontrolRSSCollector
from app.core.logging import setup_logging
from app.db.repository import IngestionRepository
from app.db.session import dispose_engine, get_session_factory, initialize_database
from app.domain.collectors import SourceMetadata
from app.services.pipeline import IngestionPipeline

log = structlog.get_logger()

FEEDS_CONFIG = [
    {
        "name": "Moneycontrol Markets",
        "url": "https://www.moneycontrol.com/rss/MCtopnews.xml",
        "collector_cls": MoneycontrolRSSCollector,
    },
    {
        "name": "Economic Times Markets",
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "collector_cls": EconomicTimesRSSCollector,
    },
    {
        "name": "LiveMint Markets",
        "url": "https://www.livemint.com/rss/markets",
        "collector_cls": LiveMintRSSCollector,
    },
    {
        "name": "Business Standard Markets",
        "url": "https://www.business-standard.com/rss/markets-106.rss",
        "collector_cls": BusinessStandardRSSCollector,
    },
    {
        "name": "CNBC TV18 Markets",
        "url": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml",
        "collector_cls": CNBCTV18RSSCollector,
    },
]


async def main():
    """Execute an end-to-end ingestion run for all RSS feeds."""
    setup_logging()
    log.info("manual_ingestion_starting")

    log.info("initializing_database")
    await initialize_database()
    log.info("database_initialized")

    # Setup repository and pipeline
    repository = IngestionRepository(get_session_factory())
    pipeline = IngestionPipeline(repository)

    collectors = []
    for feed in FEEDS_CONFIG:
        feed_id = str(uuid.uuid5(uuid.NAMESPACE_URL, feed["url"]))
        metadata = SourceMetadata(
            source_id=feed_id,
            name=feed["name"],
            url=feed["url"],
            source_type="rss",
            timezone_hint="Asia/Kolkata",
        )
        collectors.append(feed["collector_cls"](metadata))

    summary = await pipeline.run(collectors)

    print("\n" + "=" * 40)
    print(" INGESTION SUMMARY")
    print("=" * 40)
    print(f"Status:          {summary.status.value}")
    print(f"Inserted:        {summary.inserted_count}")
    print(f"Duplicates:      {summary.duplicate_count}")
    print(f"Errors:          {len(summary.errors)}")
    print(f"Failed Sources:  {len(summary.failed_sources)}")
    if summary.errors:
        print("\nErrors encountered:")
        for err in summary.errors:
            print(f" - {err}")
    print("=" * 40 + "\n")

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
