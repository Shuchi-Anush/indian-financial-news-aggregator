import os
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.article_schemas import ArticleDetail, ArticleFilters, ArticleListItem
from app.schemas.common import CursorPage
from app.services.article_read_service import ArticleReadService

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=CursorPage[ArticleListItem])
async def list_articles(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100, description="Max items per page")] = 50,
    cursor: Annotated[str | None, Query(description="Keyset pagination cursor")] = None,
    source: Annotated[list[str] | None, Query(description="Filter by source names")] = None,
    q: Annotated[str | None, Query(description="Full text search query")] = None,
    date_from: Annotated[datetime | None, Query(description="Published after date")] = None,
    date_to: Annotated[datetime | None, Query(description="Published before date")] = None,
    keywords: Annotated[str | None, Query(description="Filter by exact keywords in title")] = None,
):
    """Fetch paginated articles with optional search and filters."""
    service = ArticleReadService(db)
    filters = ArticleFilters(
        source=source,
        q=q,
        date_from=date_from,
        date_to=date_to,
        keywords=keywords,
    )
    return await service.list_articles(filters=filters, limit=limit, cursor=cursor)


@router.get("/export/csv")
async def export_articles_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    source: Annotated[list[str] | None, Query(description="Filter by source names")] = None,
    q: Annotated[str | None, Query(description="Full text search query")] = None,
    date_from: Annotated[datetime | None, Query(description="Published after date")] = None,
    date_to: Annotated[datetime | None, Query(description="Published before date")] = None,
    keywords: Annotated[str | None, Query(description="Filter by exact keywords in title")] = None,
):
    """Export filtered articles to CSV."""
    service = ArticleReadService(db)
    filters = ArticleFilters(
        source=source,
        q=q,
        date_from=date_from,
        date_to=date_to,
        keywords=keywords,
    )
    generator = await service.export_csv(filters)
    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=articles.csv"},
    )


@router.get("/export/xlsx")
async def export_articles_xlsx(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    source: Annotated[list[str] | None, Query(description="Filter by source names")] = None,
    q: Annotated[str | None, Query(description="Full text search query")] = None,
    date_from: Annotated[datetime | None, Query(description="Published after date")] = None,
    date_to: Annotated[datetime | None, Query(description="Published before date")] = None,
    keywords: Annotated[str | None, Query(description="Filter by exact keywords in title")] = None,
):
    """Export filtered articles to Excel."""
    service = ArticleReadService(db)
    filters = ArticleFilters(
        source=source,
        q=q,
        date_from=date_from,
        date_to=date_to,
        keywords=keywords,
    )
    path = await service.export_excel(filters)
    background_tasks.add_task(os.remove, path)
    return FileResponse(
        path,
        filename="articles.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(article_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    """Fetch full detail of a specific article."""
    service = ArticleReadService(db)
    return await service.get_article(article_id)
