"""Evaluates articles for duplication against known candidates.

Stateless, deterministic duplicate matching logic.
"""

from typing import Iterable

from app.domain.articles import CanonicalArticle
from app.domain.deduplication import DedupCandidate, DedupResult, SimilarityScore


class Deduplicator:
    """
    Evaluates articles for duplication against known candidates.
    Stateless, deterministic, and persistence-independent.
    """

    def __init__(self, existing_candidates: Iterable[DedupCandidate]) -> None:
        self._url_set = {c.url for c in existing_candidates}
        self._hash_set = {c.content_hash for c in existing_candidates}

    def check_duplicate(self, article: CanonicalArticle) -> DedupResult:
        """
        Check if an article is a duplicate based on exact URL or hash matches.
        """
        if article.url in self._url_set:
            return DedupResult(
                is_duplicate=True,
                matched_url=article.url,
                similarity=SimilarityScore(is_match=True, score=1.0, method="exact_url"),
            )

        if article.content_hash in self._hash_set:
            return DedupResult(
                is_duplicate=True,
                similarity=SimilarityScore(is_match=True, score=1.0, method="exact_hash"),
            )

        return DedupResult(is_duplicate=False)
