"""Logging configuration."""

import logging
import sys
from typing import Any, Dict

from app.core.config import settings


class LoggerMixin:
    """Mixin class for adding logging capabilities."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger instance."""
        return logging.getLogger(self.__class__.__name__)

    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_msg = f"{message} | {extra}" if extra else message
        self.logger.info(log_msg)

    def log_error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_msg = f"{message} | {extra}" if extra else message
        self.logger.error(log_msg)

    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_msg = f"{message} | {extra}" if extra else message
        self.logger.warning(log_msg)

    def log_debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_msg = f"{message} | {extra}" if extra else message
        self.logger.debug(log_msg)


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

