"""Observability - Logging, monitoring, and metrics.

This module provides structured logging and observability capabilities
for the application using structlog.
"""

from .logging import setup_logging, get_logger

__all__ = [
    "setup_logging",
    "get_logger",
]
