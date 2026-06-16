import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.pipeline import PipelineRunStatus


class PipelineRunResponse(BaseModel):
    """Metadata about an ingestion pipeline run."""

    id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None = None
    status: PipelineRunStatus
    articles_ingested: int
    duplicates_detected: int
    failures: int
    duration_ms: int
    failed_sources: list[str] | None = None
    errors: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)
