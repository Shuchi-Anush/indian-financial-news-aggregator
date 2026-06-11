import asyncio
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

root_dir = Path(__file__).resolve().parents[1]
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from app.core.env_loader import load_environment
load_environment()

from app.main import app
from app.db.session import initialize_database, dispose_engine

async def run_brutalization():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("--- Testing /articles ---")
        
        # 1. Invalid limits
        r = await client.get("/articles?limit=999999999999")
        print(f"Huge limit: {r.status_code}") # Should be 422
        
        r = await client.get("/articles?limit=-5")
        print(f"Negative limit: {r.status_code}") # Should be 422
        
        # 2. SQL injection attempt in query
        r = await client.get("/articles?q='; DROP TABLE articles;--")
        print(f"SQL injection search: {r.status_code}") # Should be 200, safe
        
        # 3. Invalid cursors
        r = await client.get("/articles?cursor=not-base64-cursor")
        print(f"Invalid cursor format: {r.status_code}") # Should be 400 or 422
        
        # 4. Invalid dates
        r = await client.get("/articles?start_date=invalid-date")
        print(f"Invalid start_date: {r.status_code}") # Should be 422
        
        # 5. Invalid enum
        r = await client.get("/articles?sentiment=EXTREME_HAPPINESS")
        print(f"Invalid enum sentiment: {r.status_code}") # Should be 422
        
        print("\n--- Testing /articles/export/csv ---")
        r = await client.get("/articles/export/csv?limit=50000000")
        print(f"Oversized export: {r.status_code}") # Should be bounded to max 10000 by FastAPI/Pydantic
        
        print("\n--- Testing /analytics/trending ---")
        r = await client.get("/analytics/trending?time_window_hours=-10")
        print(f"Negative time window: {r.status_code}") # Should be 422
        
        r = await client.get("/analytics/trending?time_window_hours=ABC")
        print(f"String time window: {r.status_code}") # Should be 422
        
        print("\n--- Testing missing IDs ---")
        r = await client.get("/articles/00000000-0000-0000-0000-000000000000")
        print(f"Non-existent ID: {r.status_code}") # Should be 404
        
        r = await client.get("/articles/not-a-uuid")
        print(f"Invalid UUID: {r.status_code}") # Should be 422
        
        print("\nAPI Brutalization tests completed.")

async def main():
    await initialize_database()
    try:
        await run_brutalization()
    finally:
        await dispose_engine()

if __name__ == "__main__":
    asyncio.run(main())
