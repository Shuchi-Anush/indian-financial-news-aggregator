"""Seed the DB with the Moneycontrol RSS feed if absent."""

import asyncio
import sys
import os

# Add src to path to allow direct script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import uuid
from sqlalchemy.dialects.postgresql import insert

from app.db.session import initialize_database, dispose_engine, get_session_factory
from app.models.feed_source import FeedSource, SourceType


async def seed():
    print("Initializing database...")
    await initialize_database()
    print("Database initialized.")

    url = "https://www.moneycontrol.com/rss/MCtopnews.xml"
    feed_id = uuid.uuid5(uuid.NAMESPACE_URL, url)

    session_factory = get_session_factory()
    async with session_factory() as session:
        async with session.begin():
            stmt = (
                insert(FeedSource)
                .values(
                    id=feed_id,
                    name="Moneycontrol Markets",
                    slug="moneycontrol-markets",
                    url=url,
                    source_type=SourceType.RSS,
                    timezone_hint="Asia/Kolkata",
                    is_active=True,
                    description="Top market news from Moneycontrol",
                )
                .on_conflict_do_nothing(index_elements=["url"])
            )

            result = await session.execute(stmt)
            if result.rowcount > 0:
                print(f"Inserted feed {url}")
            else:
                print(f"Feed already exists: {url}")

    print("Disposing database engine...")
    await dispose_engine()
    print("Seed process complete.")


if __name__ == "__main__":
    asyncio.run(seed())
