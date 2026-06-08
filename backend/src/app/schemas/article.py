"""Pydantic schemas for Article — API contracts and internal DTOs.

Provides:
- ``ArticleCreate`` — collector output / pipeline input (no ID, no timestamps)
- ``ArticleRead`` — full API response representation with nested feed source
- ``ArticleFilter`` — query parameter schema for filtered listing
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.article import ArticleCategory, SentimentLabel


class ArticleCreate(BaseModel):
    """Schema produced by collectors and consumed by the pipeline service.

    Collectors return ``list[ArticleCreate]`` — the pipeline service validates,
    deduplicates, and persists them.
    """

    title: str = Field(..., min_length=1, max_length=512)
    url: HttpUrl
    content_hash: str | None = Field(
        None,
        min_length=64,
        max_length=64,
        description="SHA-256 hex digest — computed by normalizer, not collector",
    )
    summary: str | None = None
    body: str | None = None
    author: str | None = Field(None, max_length=256)
    source_name: str | None = Field(None, max_length=256)
    image_url: HttpUrl | None = None
    published_at: datetime | None = None
    category: ArticleCategory | None = None
    feed_source_id: uuid.UUID | None = None


class ArticleRead(BaseModel):
    """Article API response — returned by listing and detail endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    url: str
    content_hash: str
    summary: str | None
    body: str | None
    author: str | None
    source_name: str | None
    image_url: str | None
    published_at: datetime | None
    category: ArticleCategory | None
    sentiment: SentimentLabel | None
    feed_source_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ArticleFilter(BaseModel):
    """Query parameters for filtering the article listing endpoint.

    All fields are optional — omitted fields mean "no filter".
    Used via ``Annotated[ArticleFilter, Query()]`` in route handlers.
    """

    category: ArticleCategory | None = None
    sentiment: SentimentLabel | None = None
    feed_source_id: uuid.UUID | None = None
    source_name: str | None = None
    since: datetime | None = Field(
        None, description="Return articles published after this timestamp"
    )
    until: datetime | None = Field(
        None, description="Return articles published before this timestamp"
    )
    search: str | None = Field(
        None,
        min_length=1,
        max_length=256,
        description="Full-text search against title",
    )
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
