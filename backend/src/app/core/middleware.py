"""HTTP middleware for request tracing, logging, and CORS.

Provides:
- **RequestIdMiddleware** — generates a UUID-4 per request, binds it to
  structlog context and propagates it via ``X-Request-ID`` response header.
- **RequestLoggingMiddleware** — logs method, path, status code, and
  duration for every completed request.
- **configure_cors** — sets up CORS middleware based on environment.
"""

import time
import uuid

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

log = structlog.get_logger()

REQUEST_ID_HEADER = "X-Request-ID"


# ---------------------------------------------------------------------------
# Request ID middleware
# ---------------------------------------------------------------------------


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request.

    - Reads an existing ``X-Request-ID`` header from the client, or generates one.
    - Binds it into structlog's contextvars so every log line in the request
      includes ``request_id``.
    - Echoes it back in the response headers for client-side correlation.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))

        # Bind request_id into structlog context for this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Store on request state so other layers can access it
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response


# ---------------------------------------------------------------------------
# CORS configuration
# ---------------------------------------------------------------------------


def configure_cors(app: FastAPI) -> None:
    """Add CORS middleware — permissive in dev, restricted in production."""
    settings = get_settings()

    if settings.is_production:
        origins: list[str] = []  # lock down; add explicit origins when needed
    else:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------


def register_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI application.

    Order matters — middleware added last executes first (LIFO).
    We want: RequestId → RequestLogging → CORS (outermost to innermost).
    So we register in reverse order.
    """
    configure_cors(app)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)
