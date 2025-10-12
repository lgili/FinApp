"""Logging helpers with Rich integration."""

from __future__ import annotations

import logging

from rich.logging import RichHandler

_RICH_HANDLER = RichHandler(rich_tracebacks=True, show_path=False)
_LOGGING_CONFIGURED = False


def configure_logging(level: int | str = logging.INFO) -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[_RICH_HANDLER],
    )
    _LOGGING_CONFIGURED = True


def get_logger(name: str, level: int | str | None = None) -> logging.Logger:
    configure_logging(level or logging.INFO)
    return logging.getLogger(name)
