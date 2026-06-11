"""Domain models for tracking pipeline execution runs."""

import enum
from dataclasses import dataclass
from datetime import datetime


class PipelineRunStatus(enum.Enum):
    """Execution status of an ingestion pipeline run."""

    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


@dataclass(frozen=True)
class PipelineRunResult:
    """Domain representation of a completed pipeline run."""

    started_at: datetime
    completed_at: datetime
    duration_ms: int
    articles_ingested: int
    duplicates_detected: int
    failures: int
    source_count: int
    status: PipelineRunStatus
    trigger_type: str
    error_summary: str | None = None
    failed_sources: list[str] | None = None
