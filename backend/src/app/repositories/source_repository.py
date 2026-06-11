from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feed_source import FeedSource


class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_sources(self) -> Sequence[FeedSource]:
        """Fetch all feed sources without pagination."""
        stmt = select(FeedSource).order_by(FeedSource.name.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
