from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.source_repository import SourceRepository
from app.schemas.source_schemas import SourceResponse


class SourceService:
    def __init__(self, session: AsyncSession):
        self.repo = SourceRepository(session)

    async def list_sources(self) -> Sequence[SourceResponse]:
        sources = await self.repo.list_sources()
        return [SourceResponse.model_validate(s) for s in sources]
