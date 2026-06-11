"""Article keyword extraction model.

Maps an article to its top extracted keywords.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.article import Article


class ArticleKeyword(TimestampMixin, Base):
    """Extracted keyword from an article."""

    __tablename__ = "article_keywords"
    __table_args__ = (
        Index("ix_article_keywords_article_id", "article_id"),
        Index("ix_article_keywords_keyword", "keyword"),
        Index("uq_article_keywords_article_keyword", "article_id", "keyword", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, server_default="1.0")

    article: Mapped[Article] = relationship("Article", back_populates="keywords")
