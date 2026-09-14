"""
Production Logger for Workflow Execution Engine.

Provides structured logging for:

- Workflow execution
- Node execution
- Workers
- Queue operations
- Errors
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict


class ExecutionLogger:
    """
    Central logging service.

    All execution components should use this logger.
    """


    def __init__(
        self,
        name: str = "execution-engine"
    ):

        self.logger = logging.getLogger(name)

        self.logger.setLevel(
            logging.INFO
        )


        # Prevent duplicate handlers
        if not self.logger.handlers:

            handler = logging.StreamHandler(
                sys.stdout
            )


            formatter = logging.Formatter(
                "%(asctime)s | "
                "%(levelname)s | "
                "%(name)s | "
                "%(message)s"
            )


            handler.setFormatter(
                formatter
            )


            self.logger.addHandler(
                handler
            )


    # --------------------------------------------------
    # Internal formatter
    # --------------------------------------------------

    def _format_message(
        self,
        message: str,
        metadata: Dict[str, Any] | None = None
    ):

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message
        }


        if metadata:
            payload.update(
                metadata
            )


        return str(payload)



    # --------------------------------------------------
    # Info Logs
    # --------------------------------------------------

    def info(
        self,
        message: str,
        metadata: Dict[str, Any] | None = None
    ):

        self.logger.info(
            self._format_message(
                message,
                metadata
            )
        )


    # --------------------------------------------------
    # Warning Logs
    # --------------------------------------------------

    def warning(
        self,
        message: str,
        metadata: Dict[str, Any] | None = None
    ):

        self.logger.warning(
            self._format_message(
                message,
                metadata
            )
        )


    # --------------------------------------------------
    # Error Logs
    # --------------------------------------------------

    def error(
        self,
        message: str,
        metadata: Dict[str, Any] | None = None
    ):

        self.logger.error(
            self._format_message(
                message,
                metadata
            )
        )


    # --------------------------------------------------
    # Exception Logs
    # --------------------------------------------------

    def exception(
        self,
        message: str,
        metadata: Dict[str, Any] | None = None
    ):

        self.logger.exception(
            self._format_message(
                message,
                metadata
            )
        )


# ------------------------------------------------------
# Global Logger Instance
# ------------------------------------------------------

execution_logger = ExecutionLogger()