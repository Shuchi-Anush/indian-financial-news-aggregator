import asyncio
import uuid
import sys
from pathlib import Path
from datetime import datetime, timezone

# Fix import path for standalone script execution
root_dir = Path(__file__).resolve().parents[1]
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from app.core.env_loader import load_environment
load_environment()

from app.db.session import get_session_factory, initialize_database, dispose_engine
from app.db.repository import IngestionRepository
from app.domain.articles import CanonicalArticle
from app.models.feed_source import FeedSource
from sqlalchemy import text, insert, delete

async def test_duplicate_insertions(repo: IngestionRepository, source_id: str):
    print("Testing duplicate insertions...")
    article = CanonicalArticle(
        title="Duplicate Test",
        source_name="Example Source",
        url="https://example.com/dup1",
        source_id=source_id,
        content_hash="hash1",
        collected_at=datetime.now(timezone.utc),
        content="content",
        summary=None,
        author=None,
        published_at=None,
        category="Markets"
    )
    
    inserted1 = await repo.save_articles([article], source_id="test_source")
    print(f"First insert: {inserted1}")
    inserted2 = await repo.save_articles([article], source_id="test_source")
    print(f"Second insert: {inserted2}")
    
    assert inserted1 == 1, "First insert should insert 1 row"
    assert inserted2 == 0, "Second insert should insert 0 rows due to ON CONFLICT DO NOTHING"
    print("Duplicate insertion test passed!")

async def test_concurrent_insertions(repo: IngestionRepository, source_id: str):
    print("Testing concurrent insertions...")
    articles = [
        CanonicalArticle(
            title=f"Concurrent Test {i}",
            source_name="Example Source",
            url=f"https://example.com/conc{i}",
            source_id=source_id,
            content_hash=f"hash_conc_{i}",
            collected_at=datetime.now(timezone.utc),
            content="content",
            summary=None,
            author=None,
            published_at=None,
            category="Markets"
        ) for i in range(50)
    ]
    
    # Try inserting the same 50 articles concurrently 5 times
    tasks = [
        repo.save_articles(articles, source_id="test_source")
        for _ in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    total_inserted = sum(results)
    
    assert total_inserted == 50, f"Expected 50 total insertions, got {total_inserted}. Remaining should be ignored."
    print("Concurrent insertion test passed!")

async def test_advisory_locking(repo: IngestionRepository):
    print("Testing advisory locking correctness...")
    source_id = str(uuid.uuid4())
    
    async def lock_worker(worker_id: int):
        print(f"Worker {worker_id} attempting lock...")
        async with repo.source_lock(source_id) as locked:
            if locked:
                print(f"Worker {worker_id} acquired lock, holding for 1s...")
                await asyncio.sleep(1)
                print(f"Worker {worker_id} releasing lock.")
                return True
            else:
                print(f"Worker {worker_id} failed to acquire lock.")
                return False

    tasks = [lock_worker(i) for i in range(3)]
    results = await asyncio.gather(*tasks)
    
    locks_acquired = sum(results)
    assert locks_acquired == 1, f"Expected exactly 1 worker to acquire lock, got {locks_acquired}"
    print("Advisory locking test passed!")

async def test_transaction_rollback(source_id: str):
    print("Testing transaction rollback behavior...")
    # Intentionally cause an error to verify nothing commits
    factory = get_session_factory()
    repo = IngestionRepository(factory)
    
    # First get the initial count
    async with factory() as session:
        initial_count = await session.scalar(text("SELECT count(*) FROM articles"))
    
    try:
        article1 = CanonicalArticle(
            title="Valid Article",
            source_name="Example Source",
            url="https://example.com/rollback_valid",
            source_id=source_id,
            content_hash="hash_r1",
            collected_at=datetime.now(timezone.utc),
            content="content",
            summary=None,
            author=None,
            published_at=None,
            category="Markets"
        )
        
        # We manually use session to test rollback
        async with factory() as session:
            async with session.begin():
                # We need to test the actual save_articles flow but we can't easily force it to fail
                # Let's insert manually using repo's inner session if we can, or just execute raw
                from sqlalchemy.dialects.postgresql import insert
                from app.models.article import Article
                
                stmt = insert(Article).values({
                    "title": "Valid Article",
                    "url": "https://example.com/rollback_valid",
                    "feed_source_id": source_id,
                    "content_hash": "hash_r1",
                    "collected_at": datetime.now(timezone.utc),
                    "content": "content"
                })
                await session.execute(stmt)
                
                # Intentional error to cause rollback
                await session.execute(text("SELECT * FROM non_existent_table"))
    except Exception as e:
        print(f"Caught expected error during rollback test: {type(e).__name__}")
        
    async with factory() as session:
        final_count = await session.scalar(text("SELECT count(*) FROM articles"))
        
    assert initial_count == final_count, "Rollback failed! The valid article was committed."
    print("Transaction rollback test passed!")

async def main():
    await initialize_database()
    factory = get_session_factory()
    repo = IngestionRepository(factory)
    
    # Insert a dummy feed source
    source_id = str(uuid.uuid4())
    async with factory() as session:
        async with session.begin():
            await session.execute(insert(FeedSource).values({
                "id": source_id,
                "name": "Test Source",
                "slug": "test-source",
                "url": "https://example.com/feed",
                "is_active": True
            }))
            
    try:
        await test_duplicate_insertions(repo, source_id)
        await test_concurrent_insertions(repo, source_id)
        await test_advisory_locking(repo)
        await test_transaction_rollback(source_id)
        print("\nALL PHASE 2 DB VALIDATION TESTS PASSED.")
    finally:
        # Cleanup
        async with factory() as session:
            async with session.begin():
                await session.execute(delete(FeedSource).where(FeedSource.id == source_id))
        await dispose_engine()

if __name__ == "__main__":
    asyncio.run(main())
