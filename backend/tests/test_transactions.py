from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.core.transactions import (
    InsufficientPostingsError,
    PostingCreate,
    TransactionCreate,
    UnbalancedTransactionError,
    create_transaction,
)
from finlite.db.models import Account, AccountType

EXPECTED_POSTINGS = 2


def _get_account(session: Session, account_type: AccountType) -> Account:
    stmt = select(Account).where(Account.type == account_type).limit(1)
    return session.scalars(stmt).one()


def test_create_balanced_transaction(seeded_session: Session) -> None:
    session = seeded_session
    asset = _get_account(session, AccountType.ASSET)
    expense = _get_account(session, AccountType.EXPENSE)
    payload = TransactionCreate(
        description="Coffee",
        occurred_at=datetime(2024, 5, 1, 8, 30, tzinfo=UTC),
        postings=[
            PostingCreate(account_id=asset.id, amount=Decimal("-12.50"), currency="BRL"),
            PostingCreate(account_id=expense.id, amount=Decimal("12.50"), currency="BRL"),
        ],
    )
    txn = create_transaction(session, payload)
    session.flush()
    assert txn.id is not None
    assert len(txn.postings) == EXPECTED_POSTINGS


def test_unbalanced_transaction_raises(seeded_session: Session) -> None:
    session = seeded_session
    asset = _get_account(session, AccountType.ASSET)
    expense = _get_account(session, AccountType.EXPENSE)
    payload = TransactionCreate(
        description="Broken",
        occurred_at=datetime.now(UTC),
        postings=[
            PostingCreate(account_id=asset.id, amount=Decimal("-10"), currency="BRL"),
            PostingCreate(account_id=expense.id, amount=Decimal("9"), currency="BRL"),
        ],
    )
    with pytest.raises(UnbalancedTransactionError):
        create_transaction(session, payload)


def test_transaction_requires_two_postings(seeded_session: Session) -> None:
    session = seeded_session
    asset = _get_account(session, AccountType.ASSET)
    payload = TransactionCreate(
        description="Invalid",
        occurred_at=datetime.now(UTC),
        postings=[PostingCreate(account_id=asset.id, amount=Decimal("1"), currency="BRL")],
    )
    with pytest.raises(InsufficientPostingsError):
        create_transaction(session, payload)
