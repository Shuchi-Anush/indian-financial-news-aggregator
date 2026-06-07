"""Structured logging configuration using structlog.

Provides two output modes controlled by ``APP_ENV``:
- **development** — colored, human-readable console output
- **production** — JSON lines for machine parsing

Call ``setup_logging()`` once at application startup (in ``main.py``).
After that, use ``structlog.get_logger()`` everywhere.
"""

import logging
import sys

import structlog

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure structlog and stdlib logging for the application."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Shared processors applied to every log event
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.is_production:
        # Production: JSON lines to stdout
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Development: colored console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Formatter used by stdlib handlers (uvicorn, sqlalchemy, etc.)
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    # Root handler — all stdlib loggers route through this
    root_handler = logging.StreamHandler(sys.stdout)
    root_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(root_handler)
    root_logger.setLevel(log_level)

    # Quiet down noisy third-party loggers
    for logger_name in ("uvicorn.access", "httpx", "httpcore", "asyncio"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
