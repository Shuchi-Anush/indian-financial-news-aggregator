"""Sentiment analysis processor.

Uses a deterministic financial lexicon.
"""

import re
from typing import ClassVar

from app.models.article import SentimentLabel
from app.enrichment.interfaces import EnrichmentContext, EnrichmentProcessor

class SentimentEngine(EnrichmentProcessor):
    """Calculates sentiment using bounded dictionary lookups."""

    _LEXICON: ClassVar[dict[str, float]] = {
        # Bullish / Positive
        "surge": 0.8, "jump": 0.7, "soar": 0.9, "rally": 0.8, "profit": 0.6,
        "up": 0.3, "growth": 0.5, "gain": 0.5, "outperform": 0.7,
        "upgrade": 0.6, "dividend": 0.5, "boom": 0.8, "record high": 0.9,
        "beat": 0.6, "bullish": 0.8,
        
        # Bearish / Negative
        "slump": -0.8, "plunge": -0.9, "crash": -1.0, "fall": -0.5, "drop": -0.5,
        "loss": -0.6, "decline": -0.5, "underperform": -0.7, "downgrade": -0.6,
        "fraud": -1.0, "scam": -1.0, "penalty": -0.7, "layoff": -0.8,
        "bearish": -0.8, "default": -0.9, "cut": -0.4, "miss": -0.6,
    }

    def __init__(self) -> None:
        self._pattern = re.compile(
            r"\b(" + "|".join(re.escape(word) for word in self._LEXICON.keys()) + r")\b",
            re.IGNORECASE
        )

    @property
    def name(self) -> str:
        return "sentiment_engine"

    async def process(self, context: EnrichmentContext) -> None:
        text = f"{context.article.title} {context.article.title} {context.article.content or ''}"
        
        # Bounded length
        if len(text) > 100000:
            text = text[:100000]

        matches = self._pattern.findall(text)
        if not matches:
            context.sentiment_score = 0.0
            context.sentiment_label = SentimentLabel.NEUTRAL.value
            return

        total_score = sum(self._LEXICON[m.lower()] for m in matches)
        # Normalize score between -1.0 and 1.0 using tanh-like bounded function
        # Score of +/- 2.0 pushes it close to +/- 1.0
        normalized_score = max(-1.0, min(1.0, total_score / 3.0))
        
        context.sentiment_score = round(normalized_score, 4)

        if normalized_score >= 0.2:
            context.sentiment_label = SentimentLabel.POSITIVE.value
        elif normalized_score <= -0.2:
            context.sentiment_label = SentimentLabel.NEGATIVE.value
        else:
            context.sentiment_label = SentimentLabel.NEUTRAL.value
