"""Article sector classification model.

Maps an article to a deterministic financial sector.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.article import Article


class ArticleSector(TimestampMixin, Base):
    """Extracted financial sector from an article."""

    __tablename__ = "article_sectors"
    __table_args__ = (
        Index("ix_article_sectors_article_id", "article_id"),
        Index("ix_article_sectors_sector", "sector"),
        Index("uq_article_sectors_article_sector", "article_id", "sector", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, server_default="1.0")

    article: Mapped[Article] = relationship("Article", back_populates="sectors")
