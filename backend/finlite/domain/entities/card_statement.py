"""Domain entities for credit card statements."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Iterable, Optional
from uuid import UUID, uuid4


class StatementStatus(str, Enum):
    """Possible statement statuses."""

    OPEN = "OPEN"
    PAID = "PAID"


@dataclass(frozen=True)
class CardStatementItem:
    """Individual charge inside a statement."""

    transaction_id: UUID
    occurred_at: datetime
    description: str
    amount: Decimal
    currency: str
    category_code: str
    category_name: str
    installment_number: Optional[int] = None
    installment_total: Optional[int] = None
    installment_key: Optional[str] = None


@dataclass
class CardStatementRecord:
    """Persisted statement summary."""

    id: UUID
    card_account_id: UUID
    period_start: date
    period_end: date
    closing_day: int
    due_date: date
    currency: str
    total_amount: Decimal
    items: tuple[CardStatementItem, ...]
    status: StatementStatus = StatementStatus.OPEN
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        card_account_id: UUID,
        period_start: date,
        period_end: date,
        closing_day: int,
        due_date: date,
        currency: str,
        items: Iterable[CardStatementItem],
        total_amount: Decimal,
    ) -> "CardStatementRecord":
        """Factory for new statements."""
        return cls(
            id=uuid4(),
            card_account_id=card_account_id,
            period_start=period_start,
            period_end=period_end,
            closing_day=closing_day,
            due_date=due_date,
            currency=currency,
            items=tuple(items),
            total_amount=total_amount,
        )

    def mark_paid(self) -> None:
        """Mark statement as paid."""
        self.status = StatementStatus.PAID
        self.updated_at = datetime.utcnow()
