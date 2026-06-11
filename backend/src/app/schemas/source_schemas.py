import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.feed_source import CircuitBreakerState, SourceType


class SourceResponse(BaseModel):
    """Lightweight representation of a feed source."""

    id: uuid.UUID
    name: str
    slug: str
    url: str
    source_type: SourceType
    circuit_breaker_state: CircuitBreakerState
    success_count: int
    failure_count: int
    consecutive_failures: int
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None
    health_score: float

    model_config = ConfigDict(from_attributes=True)


class SourceDetail(SourceResponse):
    """Full detail of a source including description and timestamps."""

    description: str | None = None
    created_at: datetime
    updated_at: datetime
