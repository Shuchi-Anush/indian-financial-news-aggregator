"""Date parsing utilities for RSS/Atom timestamps."""

from datetime import datetime, timezone

import structlog
from dateutil import parser as dateutil_parser

log = structlog.get_logger()


def parse_article_date(date_str: str | None, timezone_hint: str = "UTC") -> datetime | None:
    """Safely parse diverse RSS/Atom timestamp formats into timezone-aware datetimes."""
    if not date_str:
        return None

    try:
        dt = dateutil_parser.parse(date_str)
        if dt.tzinfo is None:
            import zoneinfo

            try:
                tz = zoneinfo.ZoneInfo(timezone_hint)
                dt = dt.replace(tzinfo=tz)
            except Exception:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        log.debug("date_parse_failed", raw_date=date_str, error=str(e))
        return None
