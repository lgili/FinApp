"""Transaction services enforcing double-entry constraints."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy.orm import Session

from finlite.db.models import Posting, Transaction


@dataclass(slots=True)
class PostingCreate:
    account_id: int
    amount: Decimal
    currency: str
    memo: str | None = None


@dataclass(slots=True)
class TransactionCreate:
    description: str
    occurred_at: datetime
    postings: Iterable[PostingCreate]
    reference: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class TransactionError(RuntimeError):
    """Base error for transaction operations."""


class UnbalancedTransactionError(TransactionError):
    """Raised when postings do not sum to zero."""


class InsufficientPostingsError(TransactionError):
    """Raised when fewer than two postings are provided."""


_DECIMAL_QUANT = Decimal("0.0001")
_MIN_POSTINGS = 2


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(_DECIMAL_QUANT, rounding=ROUND_HALF_UP)


def _validate_postings(postings: Iterable[PostingCreate]) -> list[PostingCreate]:
    postings_list = list(postings)
    if len(postings_list) < _MIN_POSTINGS:
        raise InsufficientPostingsError("Transactions require at least two postings")

    totals: dict[str, Decimal] = {}
    for posting in postings_list:
        totals.setdefault(posting.currency, Decimal("0"))
        totals[posting.currency] = totals[posting.currency] + _round(posting.amount)

    imbalanced = {currency: total for currency, total in totals.items() if _round(total) != 0}
    if imbalanced:
        raise UnbalancedTransactionError(f"Transaction is not balanced: {imbalanced}")

    return postings_list


def create_transaction(session: Session, payload: TransactionCreate) -> Transaction:
    postings = _validate_postings(payload.postings)
    transaction = Transaction(
        description=payload.description,
        occurred_at=payload.occurred_at,
        reference=payload.reference,
        extra=payload.extra,
    )
    session.add(transaction)
    session.flush()

    posting_models = [
        Posting(
            transaction_id=transaction.id,
            account_id=posting.account_id,
            amount=_round(posting.amount),
            currency=posting.currency,
            memo=posting.memo,
        )
        for posting in postings
    ]
    session.add_all(posting_models)
    session.flush()
    session.refresh(transaction)
    return transaction
