"""Structured logging with structlog.

This module provides structured, contextual logging for the application.
Logs can be output as JSON (production) or human-readable (development).

Examples:
    >>> from finlite.shared.observability import setup_logging, get_logger
    >>> 
    >>> # Setup (typically in main/CLI entrypoint)
    >>> setup_logging(debug=True)
    >>> 
    >>> # Use in modules
    >>> logger = get_logger(__name__)
    >>> logger.info("account_created", account_id=str(uuid4()), code="CASH001")
    >>> logger.error("validation_failed", reason="Invalid account type")
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(
    debug: bool = False,
    json_output: bool = False,
    log_level: str = "INFO",
) -> None:
    """
    Configure structured logging for the application.
    
    This sets up structlog with appropriate processors for development
    or production use. Call this once at application startup.
    
    Args:
        debug: If True, use human-readable console output with colors
        json_output: If True, output logs as JSON (useful for production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Examples:
        >>> # Development setup (colorized console)
        >>> setup_logging(debug=True)
        >>> 
        >>> # Production setup (JSON output)
        >>> setup_logging(json_output=True, log_level="WARNING")
        >>> 
        >>> # Test setup (minimal output)
        >>> setup_logging(log_level="ERROR")
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    
    # Choose processors based on environment
    processors: list[Processor] = [
        # Add log level to event dict
        structlog.processors.add_log_level,
        # Add a timestamp in ISO 8601 format
        structlog.processors.TimeStamper(fmt="iso"),
        # If the "exc_info" key is present, format the exception
        structlog.processors.format_exc_info,
        # If some value is in bytes, decode it to str
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add context variables (thread-local context)
    processors.insert(0, structlog.contextvars.merge_contextvars)
    
    # Choose final renderer
    if debug:
        # Human-readable colorized output for development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    elif json_output:
        # JSON output for production/log aggregation
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Key-value output (middle ground)
        processors.append(structlog.processors.KeyValueRenderer(key_order=["event", "level"]))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """
    Get a logger instance with optional name.
    
    Args:
        name: Optional logger name (typically __name__ of the module)
        
    Returns:
        Configured structlog logger
        
    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("operation_started", operation_id=123)
        >>> 
        >>> # With context
        >>> log = logger.bind(user_id="user123", request_id="req456")
        >>> log.info("user_action", action="create_account")
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


# Convenience function for quick logging without setup
def quick_log(
    level: str,
    message: str,
    **kwargs: Any,
) -> None:
    """
    Quick logging function for scripts/one-offs.
    
    This auto-configures logging if not already set up.
    
    Args:
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional context fields
        
    Examples:
        >>> quick_log("info", "script_started", script_name="import.py")
        >>> quick_log("error", "validation_failed", error="Invalid data")
    """
    logger = get_logger()
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, **kwargs)
