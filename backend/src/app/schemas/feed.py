"""Pydantic schemas for FeedSource — API contracts and internal DTOs.

Provides:
- ``FeedSourceCreate`` — validated input for adding a new feed
- ``FeedSourceRead`` — API response representation
- ``FeedSourceUpdate`` — partial update (all fields optional)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.feed_source import SourceType


class FeedSourceCreate(BaseModel):
    """Schema for creating a new feed source."""

    name: str = Field(..., min_length=1, max_length=256)
    slug: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe slug (lowercase, hyphens only)",
    )
    url: HttpUrl
    source_type: SourceType = SourceType.RSS
    is_active: bool = True
    description: str | None = None


class FeedSourceRead(BaseModel):
    """Schema for feed source API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    url: str
    source_type: SourceType
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime


class FeedSourceUpdate(BaseModel):
    """Schema for partial feed source updates.

    All fields are optional — only supplied fields are applied.
    """

    name: str | None = Field(None, min_length=1, max_length=256)
    url: HttpUrl | None = None
    source_type: SourceType | None = None
    is_active: bool | None = None
    description: str | None = None
