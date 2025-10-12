"""Account management services."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from finlite.db.models import Account, AccountType


@dataclass(slots=True)
class AccountCreate:
    name: str
    type: AccountType
    currency: str
    code: str | None = None
    parent_id: int | None = None


class AccountError(RuntimeError):
    """Base error for account operations."""


class AccountAlreadyExistsError(AccountError):
    """Raised when creating an account with duplicate name or code."""


def create_account(session: Session, payload: AccountCreate) -> Account:
    account = Account(
        name=payload.name,
        type=payload.type,
        currency=payload.currency,
        code=payload.code,
        parent_id=payload.parent_id,
    )
    session.add(account)
    try:
        session.flush()
    except IntegrityError as exc:  # pragma: no cover - tested via exceptions
        raise AccountAlreadyExistsError(payload.name) from exc
    return account


def list_accounts(session: Session) -> Iterable[Account]:
    return session.scalars(select(Account).order_by(Account.name)).all()


DEFAULT_CHART = (
    AccountCreate("Assets", AccountType.ASSET, "BRL"),
    AccountCreate("Liabilities", AccountType.LIABILITY, "BRL"),
    AccountCreate("Equity", AccountType.EQUITY, "BRL"),
    AccountCreate("Income", AccountType.INCOME, "BRL"),
    AccountCreate("Expenses", AccountType.EXPENSE, "BRL"),
)


def seed_default_chart(session: Session, chart: Iterable[AccountCreate] = DEFAULT_CHART) -> None:
    existing_names = {name for (name,) in session.execute(select(Account.name))}
    for entry in chart:
        if entry.name in existing_names:
            continue
        create_account(session, entry)


__all__ = [
    "AccountAlreadyExistsError",
    "AccountCreate",
    "AccountError",
    "AccountType",
    "create_account",
    "list_accounts",
    "seed_default_chart",
]
