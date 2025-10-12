"""Transaction-related domain events.

Events that occur in the lifecycle of Transaction entities.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from finlite.domain.events.base import DomainEvent


@dataclass(frozen=True)
class TransactionRecorded(DomainEvent):
    """
    Event raised when a new transaction is recorded.
    
    This is one of the most important events in a double-entry
    bookkeeping system, as every transaction changes balances.
    
    Attributes:
        transaction_id: UUID of the recorded transaction
        transaction_date: Business date of the transaction
        description: Transaction description
        total_amount: Total amount (sum of all postings, should be 0)
        posting_count: Number of postings in the transaction
        affected_accounts: List of account IDs affected by this transaction
        created_by: Optional user who recorded the transaction
        
    Examples:
        >>> event = TransactionRecorded(
        ...     transaction_id=uuid4(),
        ...     transaction_date=date(2025, 1, 15),
        ...     description="Salary payment",
        ...     total_amount=Decimal("0"),
        ...     posting_count=2,
        ...     affected_accounts=(checking_id, income_id)
        ... )
    """
    
    transaction_id: UUID
    transaction_date: date
    description: str
    total_amount: Decimal  # Should always be 0 for balanced transactions
    posting_count: int
    affected_accounts: tuple[UUID, ...]
    created_by: Optional[str] = None


@dataclass(frozen=True)
class TransactionUpdated(DomainEvent):
    """
    Event raised when a transaction is updated.
    
    Note: In proper accounting, transactions should be immutable.
    Updates should be rare and audited.
    
    Attributes:
        transaction_id: UUID of the updated transaction
        updated_fields: List of field names that were updated
        previous_description: Previous description (for audit trail)
        new_description: New description
        updated_by: Optional user who updated the transaction
    """
    
    transaction_id: UUID
    updated_fields: tuple[str, ...]
    previous_description: str
    new_description: str
    updated_by: Optional[str] = None


@dataclass(frozen=True)
class TransactionDeleted(DomainEvent):
    """
    Event raised when a transaction is deleted.
    
    Note: In proper accounting, transactions should rarely be deleted.
    Consider marking as void or creating a reversing transaction instead.
    
    Attributes:
        transaction_id: UUID of the deleted transaction
        transaction_date: Original date
        description: Original description
        reason: Reason for deletion
        deleted_by: Optional user who deleted the transaction
    """
    
    transaction_id: UUID
    transaction_date: date
    description: str
    reason: str
    deleted_by: Optional[str] = None
