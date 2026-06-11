import base64
import json
import uuid
from datetime import datetime
from typing import Any


class CursorEngine:
    """Handles opaque base64 encoding and decoding of keyset cursors."""

    @staticmethod
    def encode_cursor(
        published_at: datetime | None, record_id: uuid.UUID, rank: float | None = None
    ) -> str:
        """Encode a keyset cursor."""
        payload: dict[str, Any] = {
            "p": published_at.isoformat() if published_at else None,
            "i": str(record_id),
        }
        if rank is not None:
            payload["r"] = rank
        json_str = json.dumps(payload, separators=(",", ":"))
        return base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("utf-8").rstrip("=")

    @staticmethod
    def decode_cursor(cursor_str: str) -> dict[str, Any]:
        """Decode a keyset cursor. Raises ValueError on invalid."""
        padding = "=" * (4 - len(cursor_str) % 4)
        json_str = base64.urlsafe_b64decode(f"{cursor_str}{padding}".encode("utf-8")).decode(
            "utf-8"
        )
        payload = json.loads(json_str)

        published_at = datetime.fromisoformat(payload["p"]) if payload.get("p") else None
        record_id = uuid.UUID(payload["i"])
        rank = payload.get("r")

        return {
            "published_at": published_at,
            "id": record_id,
            "rank": float(rank) if rank is not None else None,
        }
