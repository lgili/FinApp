"""Base Domain Event class.

Domain events represent something that happened in the domain that
domain experts care about. They are immutable facts.

Examples:
    >>> from datetime import datetime
    >>> from uuid import uuid4
    >>> from dataclasses import dataclass
    >>> 
    >>> @dataclass(frozen=True)
    >>> class UserRegistered(DomainEvent):
    ...     user_id: UUID
    ...     email: str
    ...     
    >>> event = UserRegistered(user_id=uuid4(), email="user@example.com")
    >>> print(event.occurred_at)  # Automatically set
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.
    
    All domain events should:
    - Be immutable (frozen=True)
    - Have an event_id (auto-generated)
    - Have occurred_at timestamp (auto-generated)
    - Represent past tense (AccountCreated, not CreateAccount)
    
    Attributes:
        event_id: Unique identifier for this event occurrence
        occurred_at: When this event occurred
        event_type: Name of the event class (auto-populated)
        
    Examples:
        >>> @dataclass(frozen=True)
        >>> class OrderPlaced(DomainEvent):
        ...     order_id: UUID
        ...     customer_id: UUID
        ...     total: Decimal
    """
    
    # Auto-generated fields with defaults MUST come last in dataclass hierarchy
    event_id: UUID = field(default_factory=uuid4, init=False, repr=False)
    occurred_at: datetime = field(default_factory=datetime.utcnow, init=False, repr=False)
    
    @property
    def event_type(self) -> str:
        """Get the event type name."""
        return self.__class__.__name__
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.event_type}(id={self.event_id})"
