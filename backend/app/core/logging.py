"""
app/core/logging.py

Centralized application logging.

Responsibilities:

    - Configure application logging
    - Provide structured logging helpers
    - Keep logging configuration in one place
"""

from __future__ import annotations

import logging
import logging.config
import sys
from typing import Any

from app.core.config import settings


# ============================================================================
# Constants
# ============================================================================

DEFAULT_LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


# ============================================================================
# Logger configuration
# ============================================================================


def configure_logging() -> None:
    """
    Configure application-wide logging.

    Should be called once during application startup.
    """

    level = settings.log_level.upper()

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": DEFAULT_LOG_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


# ============================================================================
# Logger factory
# ============================================================================


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger for the given module.

    Usage:

        logger = get_logger(__name__)
    """

    return logging.getLogger(name)


# ============================================================================
# Structured context helper
# ============================================================================


def log_event(
    logger: logging.Logger,
    message: str,
    *,
    level: int = logging.INFO,
    **context: Any,
) -> None:
    """
    Log an event with contextual metadata.

    Example:

        log_event(
            logger,
            "Document processing started",
            document_id=document_id,
            processing_id=processing_id,
        )
    """

    if context:
        context_string = " ".join(
            f"{key}={value!r}"
            for key, value in context.items()
        )

        message = f"{message} | {context_string}"

    logger.log(level, message)