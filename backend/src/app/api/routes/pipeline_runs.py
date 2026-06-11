from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import CursorPage
from app.schemas.pipeline_schemas import PipelineRunResponse
from app.services.pipeline_read_service import PipelineReadService

router = APIRouter(prefix="/pipeline-runs", tags=["pipeline-runs"])


@router.get("", response_model=CursorPage[PipelineRunResponse])
async def list_runs(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
):
    """Fetch paginated pipeline execution runs."""
    service = PipelineReadService(db)
    return await service.list_runs(limit=limit, cursor=cursor)
