"""Event Bus - Publish/Subscribe pattern for domain events.

The Event Bus enables decoupled communication between different
parts of the application using domain events.

Examples:
    >>> bus = InMemoryEventBus()
    >>> handler = AuditLogHandler()
    >>> bus.subscribe(AccountCreated, handler)
    >>> bus.publish(AccountCreated(account_id=uuid4(), account_code="CASH001"))
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Type

from finlite.domain.events import DomainEvent


class IEventBus(ABC):
    """
    Interface for Event Bus implementations.
    
    The Event Bus pattern enables publish-subscribe communication,
    allowing components to react to events without tight coupling.
    
    Examples:
        >>> class MyEventBus(IEventBus):
        ...     def subscribe(self, event_type, handler):
        ...         # Implementation
        ...         pass
        ...     def publish(self, event):
        ...         # Implementation
        ...         pass
    """
    
    @abstractmethod
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: The event class to subscribe to
            handler: Function or handler that will process the event
            
        Examples:
            >>> bus.subscribe(AccountCreated, lambda e: print(f"Account {e.account_code} created"))
        """
        pass
    
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event: The event instance to publish
            
        Examples:
            >>> bus.publish(AccountCreated(account_id=uuid4(), account_code="CASH001"))
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The event class to unsubscribe from
            handler: The handler to remove
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Remove all subscriptions."""
        pass


class InMemoryEventBus(IEventBus):
    """
    In-memory implementation of Event Bus.
    
    This implementation stores handlers in memory and executes them
    synchronously when events are published. Suitable for most use cases.
    
    For distributed systems, consider implementing RabbitMQ or Kafka bus.
    
    Examples:
        >>> bus = InMemoryEventBus()
        >>> 
        >>> # Subscribe handlers
        >>> bus.subscribe(AccountCreated, audit_handler)
        >>> bus.subscribe(AccountCreated, notification_handler)
        >>> 
        >>> # Publish event (both handlers will be called)
        >>> bus.publish(AccountCreated(account_id=uuid4(), account_code="CASH001"))
    """
    
    def __init__(self):
        """Initialize the event bus with empty handlers."""
        self._handlers: dict[Type[DomainEvent], list[Callable[[DomainEvent], None]]] = defaultdict(list)
    
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: The event class to subscribe to
            handler: Function or handler that will process the event
        """
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Handlers are called synchronously in the order they were subscribed.
        If a handler raises an exception, it will be logged but won't stop
        other handlers from executing.
        
        Args:
            event: The event instance to publish
        """
        event_type = type(event)
        
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                # Log the error but continue processing other handlers
                # In production, use proper logging
                print(f"Error handling event {event}: {e}")
    
    def unsubscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The event class to unsubscribe from
            handler: The handler to remove
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
    
    def clear(self) -> None:
        """Remove all subscriptions."""
        self._handlers.clear()
    
    def get_handlers(self, event_type: Type[DomainEvent]) -> list[Callable[[DomainEvent], None]]:
        """
        Get all handlers for an event type (useful for testing).
        
        Args:
            event_type: The event class
            
        Returns:
            List of handlers subscribed to this event type
        """
        return self._handlers.get(event_type, []).copy()
