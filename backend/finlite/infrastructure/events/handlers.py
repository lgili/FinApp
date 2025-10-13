"""Event Handlers - React to domain events.

Handlers process events for side effects like logging, notifications,
caching updates, etc.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime

from finlite.domain.events import DomainEvent
from finlite.shared.observability import get_logger


# Initialize structured logger
logger = get_logger(__name__)


class EventHandler(ABC):
    """
    Base class for event handlers.
    
    Event handlers react to domain events and perform side effects
    such as logging, sending notifications, updating caches, etc.
    
    Examples:
        >>> class EmailNotificationHandler(EventHandler):
        ...     def handle(self, event: AccountCreated):
        ...         send_email(f"Account {event.account_code} created")
    """
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """
        Handle a domain event.
        
        Args:
            event: The domain event to handle
        """
        pass


class AuditLogHandler(EventHandler):
    """
    Handler that logs all domain events for audit purposes.
    
    This handler creates a structured audit trail of all domain events,
    which is crucial for:
    - Compliance and regulations
    - Debugging and troubleshooting
    - Event sourcing
    - Analytics
    
    Examples:
        >>> handler = AuditLogHandler()
        >>> handler.handle(AccountCreated(account_id=uuid4(), account_code="CASH001"))
        # Logs: {"event": "AccountCreated", "account_id": "...", ...}
    """
    
    def __init__(self, logger_instance=None):
        """
        Initialize the audit log handler.
        
        Args:
            logger_instance: Optional custom logger (defaults to structlog)
        """
        self.logger = logger_instance or logger
    
    def handle(self, event: DomainEvent) -> None:
        """
        Log the event to audit trail.
        
        Args:
            event: The domain event to log
        """
        # Extract event data
        event_data = {
            "event_type": event.event_type,
            "event_id": str(event.event_id),
            "occurred_at": event.occurred_at.isoformat(),
        }
        
        # Add all event-specific fields
        for key, value in event.__dict__.items():
            if key not in ("event_id", "occurred_at"):
                # Convert non-serializable types
                if isinstance(value, datetime):
                    event_data[key] = value.isoformat()
                elif hasattr(value, "__dict__"):
                    event_data[key] = str(value)
                else:
                    event_data[key] = value
        
        # Log to audit trail
        self.logger.info(
            "domain_event",
            **event_data
        )


class ConsoleEventHandler(EventHandler):
    """
    Handler that prints events to console (useful for development/debugging).
    
    Examples:
        >>> handler = ConsoleEventHandler()
        >>> handler.handle(AccountCreated(account_id=uuid4(), account_code="CASH001"))
        [EVENT] AccountCreated: account_code=CASH001
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize console handler.
        
        Args:
            verbose: If True, print full event details. If False, print summary.
        """
        self.verbose = verbose
    
    def handle(self, event: DomainEvent) -> None:
        """
        Print event to console.
        
        Args:
            event: The domain event to print
        """
        if self.verbose:
            print(f"[EVENT] {event.event_type}:")
            for key, value in event.__dict__.items():
                if key not in ("event_id", "occurred_at"):
                    print(f"  {key}: {value}")
        else:
            # Print summary
            summary_fields = []
            for key, value in event.__dict__.items():
                if key not in ("event_id", "occurred_at") and value is not None:
                    summary_fields.append(f"{key}={value}")
            
            summary = ", ".join(summary_fields[:3])  # First 3 fields
            print(f"[EVENT] {event.event_type}: {summary}")


class MetricsEventHandler(EventHandler):
    """
    Handler that tracks event metrics (counts, timing, etc.).
    
    Useful for monitoring and observability.
    
    Examples:
        >>> handler = MetricsEventHandler()
        >>> handler.handle(AccountCreated(...))
        # Increments counter: domain_events_total{event_type="AccountCreated"}
    """
    
    def __init__(self):
        """Initialize metrics handler with counters."""
        self.event_counts: dict[str, int] = {}
    
    def handle(self, event: DomainEvent) -> None:
        """
        Track event metrics.
        
        Args:
            event: The domain event to track
        """
        event_type = event.event_type
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
    
    def get_counts(self) -> dict[str, int]:
        """
        Get event counts.
        
        Returns:
            Dictionary of event_type -> count
        """
        return self.event_counts.copy()
    
    def reset(self) -> None:
        """Reset all counters."""
        self.event_counts.clear()
