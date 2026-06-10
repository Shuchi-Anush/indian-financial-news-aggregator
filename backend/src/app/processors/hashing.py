"""Deterministic hashing algorithm for canonical article verification.

Generates a stable signature based on the title and URL of an article
to support exact duplicate detection.
"""

import hashlib
import re

HASH_VERSION = "2"


def _canonicalize_text(text: str) -> str:
    """Aggressively normalize text to remove punctuation, casing, and spacing differences."""
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove non-alphanumeric chars (keep spaces)
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


def compute_content_hash(title: str, summary: str | None) -> str:
    """
    Compute a stable versioned SHA-256 hash for an article based on title and summary.
    This creates a deterministic signature for content-level exact duplicate detection.
    Prepares for future semantic hashing by heavily canonicalizing the input.
    """
    canonical_title = _canonicalize_text(title)
    canonical_summary = _canonicalize_text(summary) if summary else ""

    payload = f"v{HASH_VERSION}|{canonical_title}|{canonical_summary}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
