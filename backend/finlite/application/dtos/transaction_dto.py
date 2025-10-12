"""Transaction Data Transfer Objects."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class PostingDTO:
    """DTO for Posting output."""

    account_code: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class TransactionDTO:
    """DTO for Transaction output."""

    id: UUID
    date: date
    description: str
    postings: tuple[PostingDTO, ...]
    tags: tuple[str, ...] = ()
    payee: str | None = None
    note: str | None = None
    import_batch_id: UUID | None = None

    def is_balanced(self) -> bool:
        """Check if transaction is balanced (sum of amounts = 0)."""
        total = sum(p.amount for p in self.postings)
        return total == Decimal("0")


@dataclass(frozen=True)
class CreatePostingDTO:
    """DTO for Posting creation."""

    account_code: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class CreateTransactionDTO:
    """DTO for Transaction creation."""

    date: date
    description: str
    postings: tuple[CreatePostingDTO, ...]
    tags: tuple[str, ...] = ()
    payee: str | None = None
    note: str | None = None
    import_batch_id: UUID | None = None


@dataclass(frozen=True)
class TransactionFilterDTO:
    """DTO for filtering transactions."""

    start_date: date | None = None
    end_date: date | None = None
    account_code: str | None = None
    description: str | None = None
    tags: tuple[str, ...] = ()
    limit: int = 100
    offset: int = 0
