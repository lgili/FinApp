from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from finlite import config as config_module
from finlite.cli.app import app
from finlite.config import Settings
from finlite.core.accounts import AccountCreate, AccountType, create_account
from finlite.db import session as session_module
from finlite.db.models import Account, Posting, Transaction
from finlite.db.session import session_scope


@pytest.fixture()
def cli_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[CliRunner, Settings]]:
    data_dir = tmp_path / "finlite-data"
    monkeypatch.setenv("FINLITE_DATA_DIR", str(data_dir))
    config_module.get_settings.cache_clear()
    session_module.reset_engine()
    settings = config_module.get_settings()

    runner = CliRunner()
    try:
        yield runner, settings
    finally:
        session_module.reset_engine()
        config_module.get_settings.cache_clear()
        monkeypatch.delenv("FINLITE_DATA_DIR", raising=False)


def _get_account(session: Session, account_type: AccountType) -> Account:
    stmt = select(Account).where(Account.type == account_type).limit(1)
    return session.scalars(stmt).one()


def test_cli_income_expense_flow(cli_runner: tuple[CliRunner, Settings], tmp_path: Path) -> None:
    runner, settings = cli_runner

    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0, result.stdout

    with session_scope(settings) as session:
        expense_parent = _get_account(session, AccountType.EXPENSE)
        income_parent = _get_account(session, AccountType.INCOME)
        create_account(
            session,
            AccountCreate(
                name="Expenses:Food",
                type=AccountType.EXPENSE,
                currency="BRL",
                parent_id=expense_parent.id,
            ),
        )
        create_account(
            session,
            AccountCreate(
                name="Income:Salary",
                type=AccountType.INCOME,
                currency="BRL",
                parent_id=income_parent.id,
            ),
        )
        session.flush()

    salary_time = datetime(2025, 8, 1, 8, 0, tzinfo=UTC)
    salary_result = runner.invoke(
        app,
        [
            "txn",
            "add",
            "Salary",
            "-p",
            "Assets=1000 BRL",
            "-p",
            "Income:Salary=-1000 BRL",
            "--occurred-at",
            salary_time.isoformat(),
            "--reference",
            "payroll-2025-08",
        ],
    )
    assert salary_result.exit_code == 0, salary_result.stdout

    groceries_time = datetime(2025, 8, 15, 8, 30, tzinfo=UTC)
    expense_result = runner.invoke(
        app,
        [
            "txn",
            "add",
            "Groceries",
            "-p",
            "Assets=-200 BRL",
            "-p",
            "Expenses:Food=200 BRL",
            "--occurred-at",
            groceries_time.isoformat(),
        ],
    )
    assert expense_result.exit_code == 0, expense_result.stdout

    with session_scope(settings) as session:
        salary_txn = session.scalars(
            select(Transaction).where(Transaction.description == "Salary")
        ).one()
        groceries_txn = session.scalars(
            select(Transaction).where(Transaction.description == "Groceries")
        ).one()

        salary_amounts = {posting.amount for posting in salary_txn.postings}
        assert salary_amounts == {Decimal("1000"), Decimal("-1000")}

        groceries_amounts = {posting.amount for posting in groceries_txn.postings}
        assert groceries_amounts == {Decimal("200"), Decimal("-200")}

    report_result = runner.invoke(
        app,
        [
            "report",
            "cashflow",
            "--month",
            "2025-08",
        ],
    )
    assert report_result.exit_code == 0, report_result.stdout
    assert "Income" in report_result.stdout
    assert "1,000.00 BRL" in report_result.stdout
    assert "200.00 BRL" in report_result.stdout
    assert "800.00 BRL" in report_result.stdout

    export_path = tmp_path / "ledger.beancount"
    export_result = runner.invoke(app, ["export", "beancount", str(export_path)])
    assert export_result.exit_code == 0, export_result.stdout
    assert export_path.exists()


def test_cli_transfer_does_not_affect_cashflow(cli_runner: tuple[CliRunner, Settings]) -> None:
    runner, settings = cli_runner

    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0, result.stdout

    with session_scope(settings) as session:
        asset_parent = _get_account(session, AccountType.ASSET)
        liability_parent = _get_account(session, AccountType.LIABILITY)
        create_account(
            session,
            AccountCreate(
                name="Assets:Savings",
                type=AccountType.ASSET,
                currency="BRL",
                parent_id=asset_parent.id,
            ),
        )
        create_account(
            session,
            AccountCreate(
                name="Liabilities:Card",
                type=AccountType.LIABILITY,
                currency="BRL",
                parent_id=liability_parent.id,
            ),
        )
        session.flush()

    transfer_time = datetime(2025, 8, 5, 12, 0, tzinfo=UTC)
    transfer_result = runner.invoke(
        app,
        [
            "txn",
            "add",
            "Credit card payment",
            "-p",
            "Assets:Savings=-500 BRL",
            "-p",
            "Liabilities:Card=500 BRL",
            "--occurred-at",
            transfer_time.isoformat(),
        ],
    )
    assert transfer_result.exit_code == 0, transfer_result.stdout

    report_result = runner.invoke(app, ["report", "cashflow", "--month", "2025-08"])
    assert report_result.exit_code == 0, report_result.stdout
    assert "Income" in report_result.stdout
    assert "0.00 BRL" in report_result.stdout

    with session_scope(settings) as session:
        transactions = session.scalars(select(Transaction)).all()
        assert len(transactions) == 1
    postings = session.scalars(select(Posting)).all()
    POSTINGS_PER_TXN = 2
    assert len(postings) == POSTINGS_PER_TXN
