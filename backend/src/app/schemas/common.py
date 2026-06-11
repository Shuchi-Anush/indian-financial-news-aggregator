from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Metadata for cursor-based pagination."""

    next_cursor: str | None = Field(
        default=None, description="Opaque cursor to fetch the next page."
    )
    has_more: bool = Field(description="True if there are more items to fetch.")


class CursorPage(BaseModel, Generic[T]):
    """Generic wrapper for keyset paginated responses."""

    items: list[T]
    meta: PaginationMeta
