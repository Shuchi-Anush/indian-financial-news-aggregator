"""Quality Gate processor.

Deterministic validation layer for CanonicalArticles.
Evaluates the readiness of normalized articles before persistence.
"""

from dataclasses import dataclass
from datetime import datetime

from app.core.constants import MAX_ARTICLE_AGE_HOURS
from app.domain.articles import CanonicalArticle


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    quality_score: float
    violations: tuple[str, ...]


class QualityGate:
    """Pure validation logic to prevent low quality artifacts from persisting."""

    @staticmethod
    def validate(article: CanonicalArticle, current_utc: datetime) -> ValidationResult:
        violations = []

        # Rules
        if not article.title or len(article.title) < 5:
            violations.append("TITLE_TOO_SHORT")
        elif len(article.title) > 512:
            violations.append("TITLE_TOO_LONG")

        if not article.summary or len(article.summary.strip()) == 0:
            violations.append("SUMMARY_EMPTY")

        if not article.url or not article.url.startswith("http"):
            violations.append("URL_INVALID")

        if article.published_at:
            age_hours = (current_utc - article.published_at).total_seconds() / 3600
            if age_hours > MAX_ARTICLE_AGE_HOURS:
                violations.append("TIMESTAMP_TOO_OLD")
            elif age_hours < -1:
                violations.append("TIMESTAMP_IN_FUTURE")

        if article.author and len(article.author) > 256:
            violations.append("AUTHOR_TOO_LONG")

        # Score logic
        score = 1.0
        if "SUMMARY_EMPTY" in violations:
            score -= 0.3
        if "TITLE_TOO_SHORT" in violations:
            score -= 0.5
        if "TIMESTAMP_TOO_OLD" in violations:
            score -= 1.0

        score = max(0.0, score)

        # Critical violations flag
        critical_violations = {
            "TITLE_TOO_SHORT",
            "URL_INVALID",
            "TIMESTAMP_TOO_OLD",
            "TITLE_TOO_LONG",
            "AUTHOR_TOO_LONG",
        }
        is_valid = score >= 0.5 and not any(v in critical_violations for v in violations)

        return ValidationResult(
            is_valid=is_valid,
            quality_score=score,
            violations=tuple(violations),
        )
