"""Seed all production RSS feeds."""

import asyncio
import sys
import uuid
from pathlib import Path

# Fix import path for standalone script execution
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir / "src"))

from app.core.env_loader import load_environment

load_environment()

from sqlalchemy.dialects.postgresql import insert

from app.db.session import dispose_engine, get_session_factory, initialize_database
from app.models.feed_source import FeedSource, SourceType

FEEDS = [
    {
        "name": "Moneycontrol Markets",
        "slug": "moneycontrol-markets",
        "url": "https://www.moneycontrol.com/rss/MCtopnews.xml",
        "timezone_hint": "Asia/Kolkata",
        "description": "Top market news from Moneycontrol",
    },
    {
        "name": "Economic Times Markets",
        "slug": "economictimes-markets",
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "timezone_hint": "Asia/Kolkata",
        "description": "Market news from The Economic Times",
    },
    {
        "name": "LiveMint Markets",
        "slug": "livemint-markets",
        "url": "https://www.livemint.com/rss/markets",
        "timezone_hint": "Asia/Kolkata",
        "description": "Market news from LiveMint",
    },
    {
        "name": "Business Standard Markets",
        "slug": "business-standard-markets",
        "url": "https://www.business-standard.com/rss/markets-106.rss",
        "timezone_hint": "Asia/Kolkata",
        "description": "Market news from Business Standard",
    },
    {
        "name": "CNBC TV18 Markets",
        "slug": "cnbctv18-markets",
        "url": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml",
        "timezone_hint": "Asia/Kolkata",
        "description": "Market news from CNBC TV18",
    },
]


async def seed():
    print("Initializing database...")
    await initialize_database()
    print("Database initialized.")

    session_factory = get_session_factory()
    async with session_factory() as session:
        async with session.begin():
            for feed in FEEDS:
                feed_id = uuid.uuid5(uuid.NAMESPACE_URL, feed["url"])

                stmt = (
                    insert(FeedSource)
                    .values(
                        id=feed_id,
                        name=feed["name"],
                        slug=feed["slug"],
                        url=feed["url"],
                        source_type=SourceType.RSS,
                        timezone_hint=feed["timezone_hint"],
                        is_active=True,
                        description=feed["description"],
                    )
                    .on_conflict_do_nothing(index_elements=["url"])
                )

                result = await session.execute(stmt)
                if result.rowcount > 0:
                    print(f"Inserted feed {feed['url']}")
                else:
                    print(f"Feed already exists: {feed['url']}")

    print("Disposing database engine...")
    await dispose_engine()
    print("Seed process complete.")


if __name__ == "__main__":
    asyncio.run(seed())
