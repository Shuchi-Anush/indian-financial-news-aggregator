"""Deterministic hashing algorithm for canonical article verification.

Generates a stable signature based on the title and URL of an article
to support exact duplicate detection.
"""

import hashlib


def compute_content_hash(title: str, url: str) -> str:
    """
    Compute a stable SHA-256 hash for an article based on title and URL.
    This creates a deterministic signature for exact duplicate detection.
    """
    payload = f"{title.strip().lower()}|{url.strip().lower()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
