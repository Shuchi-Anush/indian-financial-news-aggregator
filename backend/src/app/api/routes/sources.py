from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.source_schemas import SourceResponse
from app.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
async def list_sources(response: Response, db: Annotated[AsyncSession, Depends(get_db)]):
    """Fetch all available feed sources."""
    # Light caching for sources list
    response.headers["Cache-Control"] = "public, max-age=300"
    service = SourceService(db)
    return await service.list_sources()
