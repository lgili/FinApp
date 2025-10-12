"""Account-related domain events.

Events that occur in the lifecycle of Account entities.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from finlite.domain.events.base import DomainEvent


@dataclass(frozen=True)
class AccountCreated(DomainEvent):
    """
    Event raised when a new account is created.
    
    This event is published after an account has been successfully
    persisted to the repository.
    
    Attributes:
        account_id: UUID of the created account
        account_code: Code/name of the account (e.g., "Assets:Checking")
        account_type: Type of account (ASSET, EXPENSE, etc.)
        currency: Currency code (ISO 4217)
        created_by: Optional user who created the account
        
    Examples:
        >>> event = AccountCreated(
        ...     account_id=uuid4(),
        ...     account_code="Assets:Checking",
        ...     account_type="ASSET",
        ...     currency="USD"
        ... )
    """
    
    account_id: UUID
    account_code: str
    account_type: str
    currency: str
    created_by: Optional[str] = None


@dataclass(frozen=True)
class AccountUpdated(DomainEvent):
    """
    Event raised when an account is updated.
    
    Attributes:
        account_id: UUID of the updated account
        account_code: Current code/name
        updated_fields: List of field names that were updated
        updated_by: Optional user who updated the account
    """
    
    account_id: UUID
    account_code: str
    updated_fields: tuple[str, ...]
    updated_by: Optional[str] = None


@dataclass(frozen=True)
class AccountDeactivated(DomainEvent):
    """
    Event raised when an account is deactivated.
    
    Accounts are typically deactivated rather than deleted to
    maintain historical data integrity.
    
    Attributes:
        account_id: UUID of the deactivated account
        account_code: Code/name of the account
        reason: Optional reason for deactivation
        deactivated_by: Optional user who deactivated the account
    """
    
    account_id: UUID
    account_code: str
    reason: Optional[str] = None
    deactivated_by: Optional[str] = None
