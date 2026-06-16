import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import uuid

# Re-use the env loader to get DB settings
from app.core.env_loader import load_environment
load_environment()
from app.core.config import get_settings

CANDIDATE_FEEDS = [
    {
        "name": "Economic Times Markets",
        "slug": "economic-times-markets",
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "source_type": "RSS",
        "timezone_hint": "Asia/Kolkata",
        "is_active": True
    },
    {
        "name": "LiveMint Markets",
        "slug": "livemint-markets",
        "url": "https://www.livemint.com/rss/markets",
        "source_type": "RSS",
        "timezone_hint": "Asia/Kolkata",
        "is_active": True
    },
    {
        "name": "Business Standard Markets",
        "slug": "business-standard-markets",
        "url": "https://www.business-standard.com/rss/markets-106.rss",
        "source_type": "RSS",
        "timezone_hint": "Asia/Kolkata",
        "is_active": True
    },
    {
        "name": "Moneycontrol Markets",
        "slug": "moneycontrol-markets",
        "url": "https://www.moneycontrol.com/rss/marketreports.xml",
        "source_type": "RSS",
        "timezone_hint": "Asia/Kolkata",
        "is_active": True
    },
    {
        "name": "SEBI Press Releases",
        "slug": "sebi-press-releases",
        "url": "https://www.sebi.gov.in/sebirss.xml",
        "source_type": "RSS",
        "timezone_hint": "Asia/Kolkata",
        "is_active": True
    }
]

async def seed_feeds():
    settings = get_settings()
    engine = create_async_engine(settings.effective_database_url)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    async with session_factory() as session:
        for feed in CANDIDATE_FEEDS:
            stmt = text("""
                INSERT INTO feed_sources (id, name, slug, url, source_type, timezone_hint, is_active)
                VALUES (:id, :name, :slug, :url, :source_type, :timezone_hint, :is_active)
                ON CONFLICT (slug) DO UPDATE 
                SET url = EXCLUDED.url, is_active = EXCLUDED.is_active
            """)
            await session.execute(stmt, {
                "id": uuid.uuid4(),
                "name": feed["name"],
                "slug": feed["slug"],
                "url": feed["url"],
                "source_type": feed["source_type"],
                "timezone_hint": feed["timezone_hint"],
                "is_active": feed["is_active"]
            })
            print(f"Seeded: {feed['name']} ({feed['slug']})")
        
        await session.commit()
    await engine.dispose()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_feeds())
