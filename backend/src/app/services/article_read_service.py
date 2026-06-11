import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.exporters.csv_exporter import CSVExporter
from app.exporters.excel_exporter import ExcelExporter
from app.repositories.article_repository import ArticleRepository
from app.schemas.article_schemas import ArticleDetail, ArticleFilters, ArticleListItem
from app.schemas.common import CursorPage, PaginationMeta
from app.utils.cursor import CursorEngine


class ArticleReadService:
    def __init__(self, session: AsyncSession):
        self.repo = ArticleRepository(session)

    async def list_articles(
        self, filters: ArticleFilters, limit: int = 50, cursor: str | None = None
    ) -> CursorPage[ArticleListItem]:

        cursor_data = None
        if cursor:
            try:
                cursor_data = CursorEngine.decode_cursor(cursor)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid cursor format")

        # Repo fetches limit + 1
        rows = await self.repo.list_articles(filters, limit, cursor_data)

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = []
        for row in rows:
            # Map Row tuple to schema
            item = ArticleListItem.model_validate(row)
            items.append(item)

        next_cursor = None
        if items and has_more:
            last_item = items[-1]
            last_row = rows[-1]
            rank = getattr(last_row, "rank", None)
            next_cursor = CursorEngine.encode_cursor(
                published_at=last_item.published_at, record_id=last_item.id, rank=rank
            )

        return CursorPage(
            items=items, meta=PaginationMeta(next_cursor=next_cursor, has_more=has_more)
        )

    async def get_article(self, article_id: uuid.UUID) -> ArticleDetail:
        article = await self.repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return ArticleDetail.model_validate(article)

    async def _validate_export_size(self, filters: ArticleFilters) -> None:
        count = await self.repo.count_articles(filters)
        if count > 10000:
            raise HTTPException(
                status_code=400,
                detail=f"Export too large ({count} rows). Maximum allowed is 10,000.",
            )

    async def export_csv(self, filters: ArticleFilters):
        await self._validate_export_size(filters)
        generator = self.repo.stream_articles(filters, chunk_size=1000, include_summary=True)
        exporter = CSVExporter()
        return exporter.export(generator)

    async def export_excel(self, filters: ArticleFilters) -> str:
        await self._validate_export_size(filters)
        generator = self.repo.stream_articles(filters, chunk_size=1000, include_summary=True)
        exporter = ExcelExporter()
        return await exporter.export(generator)
