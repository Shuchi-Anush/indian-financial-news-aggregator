"""Domain models for tracking pipeline execution runs."""

import enum
from dataclasses import dataclass
from datetime import datetime


class PipelineRunStatus(enum.Enum):
    """Execution status of an ingestion pipeline run."""

    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


@dataclass(frozen=True)
class PipelineRunResult:
    """Domain representation of a completed pipeline run."""

    started_at: datetime
    completed_at: datetime
    status: PipelineRunStatus
    inserted_count: int
    duplicate_count: int
    failed_sources: tuple[str, ...]
    errors: tuple[str, ...]
