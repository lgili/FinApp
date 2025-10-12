from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.core.accounts import AccountCreate, AccountType, create_account
from finlite.core.transactions import PostingCreate, TransactionCreate, create_transaction
from finlite.db.models import Account
from finlite.reports.cashflow import generate_cashflow


def _get_account(session: Session, account_type: AccountType) -> Account:
    stmt = select(Account).where(Account.type == account_type).limit(1)
    return session.scalars(stmt).one()


def _record_transaction(
    session: Session,
    description: str,
    postings: list[PostingCreate],
    occurred_at: datetime,
) -> None:
    create_transaction(
        session,
        TransactionCreate(description=description, occurred_at=occurred_at, postings=postings),
    )
    session.flush()


def test_cashflow_report_income_and_expense(seeded_session: Session) -> None:
    session = seeded_session
    asset = _get_account(session, AccountType.ASSET)
    income = _get_account(session, AccountType.INCOME)
    expense = _get_account(session, AccountType.EXPENSE)

    occurred = datetime(2025, 8, 15, tzinfo=UTC)

    _record_transaction(
        session,
        "Salary",
        [
            PostingCreate(account_id=asset.id, amount=Decimal("1000"), currency="BRL"),
            PostingCreate(account_id=income.id, amount=Decimal("-1000"), currency="BRL"),
        ],
        occurred,
    )

    _record_transaction(
        session,
        "Groceries",
        [
            PostingCreate(account_id=asset.id, amount=Decimal("-200"), currency="BRL"),
            PostingCreate(account_id=expense.id, amount=Decimal("200"), currency="BRL"),
        ],
        occurred,
    )

    report = generate_cashflow(
        session,
        datetime(2025, 8, 1, tzinfo=UTC),
        datetime(2025, 9, 1, tzinfo=UTC),
        "BRL",
    )

    assert report.income.total == Decimal("1000.00")
    assert report.expenses.total == Decimal("200.00")
    assert report.net == Decimal("800.00")
    assert [(row.account_name, row.amount) for row in report.income.rows] == [
        (income.name, Decimal("1000.00"))
    ]
    assert [(row.account_name, row.amount) for row in report.expenses.rows] == [
        (expense.name, Decimal("200.00"))
    ]


def test_cashflow_report_filters_currency(seeded_session: Session) -> None:
    session = seeded_session
    asset = _get_account(session, AccountType.ASSET)
    income = _get_account(session, AccountType.INCOME)

    occurred = datetime(2025, 7, 10, tzinfo=UTC)

    _record_transaction(
        session,
        "Freelance",
        [
            PostingCreate(account_id=asset.id, amount=Decimal("500"), currency="USD"),
            PostingCreate(account_id=income.id, amount=Decimal("-500"), currency="USD"),
        ],
        occurred,
    )

    report = generate_cashflow(
        session,
        datetime(2025, 7, 1, tzinfo=UTC),
        datetime(2025, 8, 1, tzinfo=UTC),
        "BRL",
    )

    assert report.income.total == Decimal("0.00")
    assert report.expenses.total == Decimal("0.00")
    assert report.net == Decimal("0.00")


def test_cashflow_ignores_non_income_expense_accounts(seeded_session: Session) -> None:
    session = seeded_session
    asset_primary = _get_account(session, AccountType.ASSET)
    asset_secondary = create_account(
        session,
        AccountCreate(
            name="Assets:Savings",
            type=AccountType.ASSET,
            currency="BRL",
            parent_id=asset_primary.id,
        ),
    )

    occurred = datetime(2025, 6, 20, tzinfo=UTC)

    _record_transaction(
        session,
        "Transfer",
        [
            PostingCreate(account_id=asset_primary.id, amount=Decimal("-300"), currency="BRL"),
            PostingCreate(account_id=asset_secondary.id, amount=Decimal("300"), currency="BRL"),
        ],
        occurred,
    )

    report = generate_cashflow(
        session,
        datetime(2025, 6, 1, tzinfo=UTC),
        datetime(2025, 7, 1, tzinfo=UTC),
        "BRL",
    )

    assert report.income.total == Decimal("0.00")
    assert report.expenses.total == Decimal("0.00")
    assert report.net == Decimal("0.00")
