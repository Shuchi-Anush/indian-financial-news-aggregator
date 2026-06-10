import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir / "src"))

import asyncio
from app.core.env_loader import load_environment
load_environment()

from app.db.session import initialize_database
from app.core.metrics import export_metrics

async def main():
    await initialize_database()
    output = await export_metrics()
    print("OUTPUT IS:", repr(output))

if __name__ == "__main__":
    asyncio.run(main())
