"""Immutable domain entities representing deduplication matches.

Defines the structure for duplicate candidates and comparison outcomes.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DedupCandidate:
    """A minimal article representation used for deduplication comparisons."""

    url: str
    content_hash: str


@dataclass(frozen=True)
class SimilarityScore:
    """Result of a similarity comparison between two items."""

    is_match: bool
    score: float
    method: str


@dataclass(frozen=True)
class DedupResult:
    """Outcome of a deduplication check."""

    is_duplicate: bool
    matched_url: Optional[str] = None
    similarity: Optional[SimilarityScore] = None
