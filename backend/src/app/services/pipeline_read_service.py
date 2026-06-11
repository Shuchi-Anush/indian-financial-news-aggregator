from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.common import CursorPage, PaginationMeta
from app.schemas.pipeline_schemas import PipelineRunResponse
from app.utils.cursor import CursorEngine


class PipelineReadService:
    def __init__(self, session: AsyncSession):
        self.repo = PipelineRepository(session)

    async def list_runs(
        self, limit: int = 50, cursor: str | None = None
    ) -> CursorPage[PipelineRunResponse]:
        cursor_data = None
        if cursor:
            try:
                cursor_data = CursorEngine.decode_cursor(cursor)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid cursor format")

        rows = await self.repo.list_runs(limit, cursor_data)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [PipelineRunResponse.model_validate(row) for row in rows]

        next_cursor = None
        if items and has_more:
            last_item = items[-1]
            next_cursor = CursorEngine.encode_cursor(
                published_at=last_item.started_at, record_id=last_item.id
            )

        return CursorPage(
            items=items, meta=PaginationMeta(next_cursor=next_cursor, has_more=has_more)
        )
