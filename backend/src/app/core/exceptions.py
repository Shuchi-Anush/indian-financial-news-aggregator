"""Domain exception hierarchy and FastAPI exception handlers.

All business-logic errors should use these domain exceptions instead of
bare ``ValueError`` / ``RuntimeError``. The FastAPI handlers at the bottom
of this module translate them into consistent JSON error responses.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------


class AppError(Exception):
    """Base exception for all application domain errors.

    Subclasses set ``status_code`` and ``error_code`` to control the HTTP
    response produced by the exception handler.
    """

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Domain-specific exceptions
# ---------------------------------------------------------------------------


class NotFoundError(AppError):
    """Requested entity does not exist."""

    status_code = 404
    error_code = "not_found"

    def __init__(
        self,
        message: str = "Resource not found",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class CollectorError(AppError):
    """RSS feed or API collector failure."""

    status_code = 502
    error_code = "collector_error"

    def __init__(
        self,
        message: str = "Collector failed",
        *,
        source: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = {**(details or {}), "source": source} if source else (details or {})
        super().__init__(message, details=_details)


class NormalizationError(AppError):
    """Article normalization / cleaning failure."""

    status_code = 422
    error_code = "normalization_error"


class DuplicateArticleError(AppError):
    """Article was identified as a duplicate (non-fatal in pipeline context)."""

    status_code = 409
    error_code = "duplicate_article"


class ExportError(AppError):
    """CSV / Excel export generation failure."""

    status_code = 500
    error_code = "export_error"


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------


def _build_error_response(exc: AppError) -> JSONResponse:
    """Convert a domain exception into a consistent JSON response."""
    body: dict[str, Any] = {
        "error": exc.error_code,
        "message": exc.message,
    }
    if exc.details:
        body["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=body)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Handle all AppError subclasses with structured JSON responses."""
    return _build_error_response(exc)


async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions — returns a generic 500."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected internal error occurred",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
