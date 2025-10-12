from __future__ import annotations

from sqlalchemy.orm import Session

from finlite.core.accounts import (
    AccountCreate,
    AccountType,
    create_account,
    list_accounts,
    seed_default_chart,
)
from finlite.db.models import Account


def test_create_account(session: Session) -> None:
    payload = AccountCreate(name="Test", type=AccountType.ASSET, currency="BRL")
    account = create_account(session, payload)
    session.flush()
    fetched = session.get(Account, account.id)
    assert fetched is not None
    assert fetched.name == "Test"
    assert fetched.type == AccountType.ASSET


def test_seed_default_chart_idempotent(session: Session) -> None:
    seed_default_chart(session)
    first = list(list_accounts(session))
    seed_default_chart(session)
    second = list(list_accounts(session))
    assert len(first) == len(second)
    assert {acc.name for acc in first} == {acc.name for acc in second}
