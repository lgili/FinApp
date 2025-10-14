"""Compatibility shim: re-export event bus classes.

Some examples and modules import from `finlite.shared.event_bus`.
The canonical implementation lives in `finlite.infrastructure.events.event_bus`.
This file re-exports the public symbols so older import paths keep working.
"""

from finlite.infrastructure.events.event_bus import IEventBus, InMemoryEventBus

__all__ = ["IEventBus", "InMemoryEventBus"]
