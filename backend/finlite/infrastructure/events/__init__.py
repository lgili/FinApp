"""Event Bus - Infrastructure for domain events.

Event Bus pattern enables publish-subscribe communication between
different parts of the application without tight coupling.
"""

from .event_bus import IEventBus, InMemoryEventBus
from .handlers import AuditLogHandler, EventHandler

__all__ = [
    "IEventBus",
    "InMemoryEventBus",
    "EventHandler",
    "AuditLogHandler",
]
