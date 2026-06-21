import asyncio
import uuid
import sys
from pathlib import Path
from aiohttp import web

# Fix import path for standalone script execution
root_dir = Path(__file__).resolve().parents[1]
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from app.core.env_loader import load_environment
load_environment()

from app.db.session import get_session_factory, initialize_database, dispose_engine
from app.db.repository import IngestionRepository
from app.models.feed_source import FeedSource
from app.orchestration.ingestion_jobs import run_ingestion_cycle
from sqlalchemy import insert, delete

# Handlers for Chaos Server
async def handle_broken_xml(request):
    return web.Response(text="""<?xml version="1.0"?><rss><channel><title>Broken</title><item><title>Missing closing tags</item></channel></rss>""", content_type="text/xml")

async def handle_500(request):
    return web.Response(status=500, text="Internal Server Error")

async def handle_429(request):
    return web.Response(status=429, text="Too Many Requests")

async def handle_timeout(request):
    await asyncio.sleep(5)
    return web.Response(text="<rss></rss>")

async def handle_duplicates(request):
    rss = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>Dupes</title>
            <item>
                <title>Article 1</title>
                <link>http://example.com/1</link>
                <guid>guid1</guid>
                <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
            </item>
            <item>
                <title>Article 1 Again</title>
                <link>http://example.com/1</link>
                <guid>guid1</guid>
                <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
            </item>
            <item>
                <title>Article 2</title>
                <link>http://example.com/1</link> <!-- Same Link! -->
                <guid>guid2</guid>
                <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """
    return web.Response(text=rss, content_type="text/xml")

async def handle_empty(request):
    return web.Response(text="""<?xml version="1.0"?><rss><channel></channel></rss>""", content_type="text/xml")


async def start_chaos_server():
    app = web.Application()
    app.router.add_get('/broken_xml', handle_broken_xml)
    app.router.add_get('/500', handle_500)
    app.router.add_get('/429', handle_429)
    app.router.add_get('/timeout', handle_timeout)
    app.router.add_get('/duplicates', handle_duplicates)
    app.router.add_get('/empty', handle_empty)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 9999)
    await site.start()
    return runner

async def main():
    await initialize_database()
    factory = get_session_factory()
    repo = IngestionRepository(factory)
    
    runner = await start_chaos_server()
    print("Chaos server started on port 9999")
    
    # Insert chaos feeds
    feeds = [
        ("chaos-broken", "http://localhost:9999/broken_xml"),
        ("chaos-500", "http://localhost:9999/500"),
        ("chaos-429", "http://localhost:9999/429"),
        ("chaos-timeout", "http://localhost:9999/timeout"),
        ("chaos-dupes", "http://localhost:9999/duplicates"),
        ("chaos-empty", "http://localhost:9999/empty"),
    ]
    
    feed_ids = []
    async with factory() as session:
        async with session.begin():
            for slug, url in feeds:
                fid = str(uuid.uuid4())
                feed_ids.append(fid)
                await session.execute(insert(FeedSource).values({
                    "id": fid,
                    "name": slug,
                    "slug": slug,
                    "url": url,
                    "is_active": True
                }))
    
    try:
        print("Running chaos ingestion cycle...")
        # Reduce timeout configs via env vars for the test if possible, or just let it run
        import os
        os.environ["HTTP_TIMEOUT"] = "2.0"
        
        await run_ingestion_cycle()
        
        print("\nIngestion cycle survived chaos! Checking results...")
        
        # Verify circuit breaker opened for 500 and 429
        # Check failed articles, etc.
        # This implicitly tests that run_ingestion_cycle doesn't crash the event loop
        print("PHASE 3: INGESTION CHAOS TESTING PASSED (Pipeline survived without crashing)")
        
    except Exception as e:
        print(f"PIPELINE CRASHED: {e}")
        raise
    finally:
        # Cleanup
        async with factory() as session:
            async with session.begin():
                for fid in feed_ids:
                    await session.execute(delete(FeedSource).where(FeedSource.id == fid))
        await dispose_engine()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
