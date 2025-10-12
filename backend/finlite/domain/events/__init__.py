"""Domain Events - Event-driven architecture support.

Domain events represent things that have happened in the domain that
domain experts care about. They enable loose coupling and auditability.

Examples:
    >>> event = AccountCreated(account_id=uuid4(), account_code="CASH001")
    >>> event_bus.publish(event)
"""

from .base import DomainEvent
from .account_events import AccountCreated, AccountUpdated, AccountDeactivated
from .transaction_events import TransactionRecorded, TransactionUpdated, TransactionDeleted

__all__ = [
    # Base
    "DomainEvent",
    # Account events
    "AccountCreated",
    "AccountUpdated",
    "AccountDeactivated",
    # Transaction events
    "TransactionRecorded",
    "TransactionUpdated",
    "TransactionDeleted",
]
