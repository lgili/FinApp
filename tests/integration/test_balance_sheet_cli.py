"""Integration test for the balance sheet CLI command."""

import re
from datetime import date
from decimal import Decimal
import importlib

from typer.testing import CliRunner

from finlite.application.dtos import CreateAccountDTO, CreatePostingDTO, CreateTransactionDTO
from finlite.shared.di import create_container, init_database

CLI_APP_MODULE = importlib.import_module("finlite.interfaces.cli.app")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text for easier assertions."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_balance_sheet_cli_summary(tmp_path, monkeypatch):
    """The CLI should render balance sheet totals for the requested date."""
    db_path = tmp_path / "cli-balance.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    create_account = container.create_account_use_case()
    create_account.execute(
        CreateAccountDTO(
            code="Assets:Bank:Checking",
            name="Assets:Bank:Checking",
            type="ASSET",
            currency="BRL",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Liabilities:CreditCard",
            name="Liabilities:CreditCard",
            type="LIABILITY",
            currency="BRL",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Equity:OpeningBalances",
            name="Equity:OpeningBalances",
            type="EQUITY",
            currency="BRL",
        )
    )

    record_transaction = container.record_transaction_use_case()
    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 1, 1),
            description="Opening capital",
            postings=(
                CreatePostingDTO("Assets:Bank:Checking", Decimal("5000"), "BRL"),
                CreatePostingDTO("Equity:OpeningBalances", Decimal("-5000"), "BRL"),
            ),
        )
    )
    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 1, 15),
            description="Loan deposit",
            postings=(
                CreatePostingDTO("Assets:Bank:Checking", Decimal("2000"), "BRL"),
                CreatePostingDTO("Liabilities:CreditCard", Decimal("-2000"), "BRL"),
            ),
        )
    )

    # Ensure CLI reuses this container instance
    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    runner = CliRunner()
    result = runner.invoke(
        CLI_APP_MODULE.app,
        ["reports", "balance-sheet", "--at", "2024-01-31", "--currency", "BRL", "--summary"],
    )

    assert result.exit_code == 0, result.stdout
    output = strip_ansi(result.stdout)

    assert "Assets" in output
    assert "7,000.00 BRL" in output
    assert "Liabilities" in output
    assert "2,000.00 BRL" in output
    assert "Net Worth" in output
    assert "5,000.00 BRL" in output
