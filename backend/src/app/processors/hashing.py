"""Deterministic hashing algorithm for canonical article verification.

Generates a stable signature based on the title and URL of an article
to support exact duplicate detection.
"""

import hashlib


HASH_VERSION = "1"


def compute_content_hash(title: str, summary: str | None) -> str:
    """
    Compute a stable versioned SHA-256 hash for an article based on title and summary.
    This creates a deterministic signature for content-level exact duplicate detection.
    """
    safe_summary = summary.strip().lower() if summary else ""
    payload = f"v{HASH_VERSION}|{title.strip().lower()}|{safe_summary}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
