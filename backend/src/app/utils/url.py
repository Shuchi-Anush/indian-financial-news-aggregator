"""URL normalization utilities."""

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# Common tracking parameters to strip from URLs
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "_ga",
    "mc_cid",
    "mc_eid",
}


def normalize_url(url: str) -> str:
    """
    Robust URL normalization:
    - Lowercase hostname
    - Strip tracking query parameters
    - Normalize trailing slashes (keep canonical paths)
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url.strip())

        # Lowercase hostname
        netloc = parsed.netloc.lower()

        # Preserve canonical paths, but remove trailing slash if it's just the root domain,
        # or keep consistent handling. Actually, typical normalization removes trailing slashes from paths.
        path = parsed.path
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        # Strip tracking params
        if parsed.query:
            query_params = parse_qsl(parsed.query, keep_blank_values=True)
            filtered_params = [(k, v) for k, v in query_params if k.lower() not in TRACKING_PARAMS]
            query = urlencode(filtered_params)
        else:
            query = ""

        return urlunparse((parsed.scheme.lower(), netloc, path, parsed.params, query, ""))
    except Exception:
        return url.strip()
