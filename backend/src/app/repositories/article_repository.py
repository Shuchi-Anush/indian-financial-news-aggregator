import uuid
from typing import Any, Sequence

from sqlalchemy import and_, func, nulls_last, or_, select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.schemas.article_schemas import ArticleFilters


class ArticleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, article_id: uuid.UUID) -> Article | None:
        """Fetch full article detail."""
        stmt = select(Article).where(Article.id == article_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_insert_articles(self, articles: Sequence[dict[str, Any]]) -> int:
        """
        Bulk insert articles using PostgreSQL ON CONFLICT DO NOTHING.
        Relies on the unique constraint on (url) or (content_hash) defined in the model.
        Returns the number of rows actually inserted.
        """
        if not articles:
            return 0

        from sqlalchemy.dialects.postgresql import insert
        
        stmt = insert(Article).values(articles)
        # Assuming URL is uniquely constrained. We do nothing on conflict.
        stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
        
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore[attr-defined]

    async def count_articles(self, filters: ArticleFilters) -> int:
        """Count articles matching the given filters."""
        stmt = select(func.count(Article.id))

        stmt = self._apply_filters(stmt, filters)

        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def list_articles(
        self,
        filters: ArticleFilters,
        limit: int,
        cursor_data: dict[str, Any] | None = None,
        include_summary: bool = False,
    ) -> Sequence[Row]:
        """Fetch a page of articles (limit + 1 for has_more logic)."""

        # Explicit projection (No content/body)
        cols = [
            Article.id,
            Article.title,
            Article.url,
            Article.author,
            Article.source_name,
            Article.image_url,
            Article.published_at,
            Article.category,
            Article.sentiment,
        ]

        if include_summary:
            cols.append(Article.summary)

        stmt = select(*cols)

        stmt = self._apply_filters(stmt, filters)
        
        is_search = bool(filters.search)
        rank_col = None

        if is_search:
            tsquery = func.websearch_to_tsquery("english", filters.search)
            rank_col = func.ts_rank(Article.search_vector, tsquery).label("rank")
            stmt = stmt.add_columns(rank_col)

        # Keyset Pagination Conditions & Sorting
        if is_search:
            assert rank_col is not None
            # Sort: rank DESC, published_at DESC, id DESC
            stmt = stmt.order_by(
                rank_col.desc(), nulls_last(Article.published_at.desc()), Article.id.desc()
            )

            if cursor_data:
                c_rank = cursor_data.get("rank", 0.0)
                c_pub = cursor_data["published_at"]
                c_id = cursor_data["id"]

                # Keyset logic for (rank DESC, published_at DESC, id DESC)
                if c_pub is not None:
                    stmt = stmt.where(
                        or_(
                            rank_col < c_rank,
                            and_(rank_col == c_rank, Article.published_at < c_pub),
                            and_(
                                rank_col == c_rank, Article.published_at == c_pub, Article.id < c_id
                            ),
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            rank_col < c_rank,
                            and_(
                                rank_col == c_rank,
                                Article.published_at.is_(None),
                                Article.id < c_id,
                            ),
                            and_(rank_col == c_rank, Article.published_at.isnot(None)),
                        )
                    )
        else:
            # Default Sort: published_at DESC, id DESC
            stmt = stmt.order_by(nulls_last(Article.published_at.desc()), Article.id.desc())

            if cursor_data:
                c_pub = cursor_data["published_at"]
                c_id = cursor_data["id"]

                if c_pub is not None:
                    stmt = stmt.where(
                        or_(
                            Article.published_at < c_pub,
                            and_(Article.published_at == c_pub, Article.id < c_id),
                        )
                    )
                else:
                    # If cursor published_at is None, we are in the NULLs section
                    # NULLs come last, so anything with a timestamp is "greater"
                    stmt = stmt.where(
                        or_(
                            and_(Article.published_at.is_(None), Article.id < c_id),
                            # Since we want published_at DESC nulls_last, if cursor has None,
                            # we only return other Nones with a smaller ID. We don't return non-Nones.
                        )
                    )

        # limit + 1
        stmt = stmt.limit(limit + 1)
        result = await self.session.execute(stmt)
        return result.all()

    async def stream_articles(
        self,
        filters: ArticleFilters,
        chunk_size: int = 1000,
        include_summary: bool = False,
    ):
        """Iterate over articles safely in chunks using keyset pagination."""
        # Note: We must NOT use OFFSET. We manually track cursor state internally.
        cursor_data = None

        while True:
            chunk = await self.list_articles(
                filters=filters,
                limit=chunk_size,
                cursor_data=cursor_data,
                include_summary=include_summary,
            )

            # Since limit + 1 is returned by list_articles if has_more is true,
            # we need to pop the last element if it exceeds chunk_size, or just process it.
            # Actually list_articles returns up to limit + 1 elements.
            has_more = len(chunk) > chunk_size
            if has_more:
                yield chunk[:chunk_size]
                last_item = chunk[chunk_size - 1]
                cursor_data = {
                    "published_at": last_item.published_at,
                    "id": last_item.id,
                }
                if hasattr(last_item, "rank"):
                    cursor_data["rank"] = last_item.rank
            else:
                if chunk:
                    yield chunk
                break

    def _apply_filters(self, stmt: Any, filters: ArticleFilters) -> Any:
        if filters.source_names:
            stmt = stmt.where(Article.source_name.in_(filters.source_names))
        if filters.published_after:
            stmt = stmt.where(Article.published_at >= filters.published_after)
        if filters.published_before:
            stmt = stmt.where(Article.published_at <= filters.published_before)
        if filters.keywords:
            stmt = stmt.where(Article.title.ilike(f"%{filters.keywords}%"))
            
        if filters.search:
            tsquery = func.websearch_to_tsquery("english", filters.search)
            stmt = stmt.where(Article.search_vector.op("@@")(tsquery))

        if getattr(filters, "sentiment", None):
            stmt = stmt.where(Article.sentiment_label == filters.sentiment)

        # Advanced EXISTS queries for enrichment lists
        if getattr(filters, "entity", None):
            from app.models.article_entity import ArticleEntity
            stmt = stmt.where(
                Article.id.in_(
                    select(ArticleEntity.article_id).where(ArticleEntity.entity == filters.entity)
                )
            )
            
        if getattr(filters, "sector", None):
            from app.models.article_sector import ArticleSector
            stmt = stmt.where(
                Article.id.in_(
                    select(ArticleSector.article_id).where(ArticleSector.sector == filters.sector)
                )
            )
            
        if getattr(filters, "extracted_keyword", None):
            from app.models.article_keyword import ArticleKeyword
            stmt = stmt.where(
                Article.id.in_(
                    select(ArticleKeyword.article_id).where(ArticleKeyword.keyword == filters.extracted_keyword)
                )
            )

        return stmt
