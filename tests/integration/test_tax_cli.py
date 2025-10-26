"""Integration tests for tax CLI commands."""

import csv
import importlib
from datetime import date
from decimal import Decimal

from typer.testing import CliRunner

from finlite.application.dtos import (
    CreateAccountDTO,
    CreatePostingDTO,
    CreateTransactionDTO,
)
from finlite.shared.di import create_container, init_database


def test_monthly_tax_cli_summary(tmp_path, monkeypatch):
    container = create_container(f"sqlite:///{tmp_path/'tax.db'}", echo=False)
    init_database(container)

    create_account = container.create_account_use_case()
    # Minimal accounts for recording transactions
    create_account.execute(
        CreateAccountDTO(
            code="Assets:Brokerage:Cash",
            name="Assets:Brokerage:Cash",
            type="ASSET",
            currency="BRL",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Income:CapitalGains",
            name="Income:CapitalGains",
            type="INCOME",
            currency="BRL",
        )
    )

    record_transaction = container.record_transaction_use_case()

    # September loss generates carryover
    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2025, 9, 15),
            description="September Loss",
            postings=(
                CreatePostingDTO("Assets:Brokerage:Cash", Decimal("10000"), "BRL"),
                CreatePostingDTO("Income:CapitalGains", Decimal("-10000"), "BRL"),
            ),
            tags=(
                "tax:sale=30000",
                "tax:loss=2000",
                "tax:currency=BRL",
            ),
        )
    )

    # October gain consumes carryover
    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2025, 10, 20),
            description="October Gain",
            postings=(
                CreatePostingDTO("Assets:Brokerage:Cash", Decimal("12000"), "BRL"),
                CreatePostingDTO("Income:CapitalGains", Decimal("-12000"), "BRL"),
            ),
            tags=(
                "tax:sale=45000",
                "tax:gain=7000",
                "tax:withheld=200",
                "tax:dividend=500",
                "tax:jcp=150",
                "tax:currency=BRL",
            ),
        )
    )

    cli_app_module = importlib.import_module("finlite.interfaces.cli.app")
    monkeypatch.setattr(cli_app_module, "_container", container, raising=False)

    runner = CliRunner()
    result = runner.invoke(
        cli_app_module.app,
        ["tax", "monthly", "--month", "2025-10"],
    )

    assert result.exit_code == 0, result.stdout
    output = result.stdout
    assert "Total Sales" in output
    assert "45,000.00" in output
    assert "DARF Payable" in output

    export_path = tmp_path / "tax-oct.csv"
    export_result = runner.invoke(
        cli_app_module.app,
        [
            "tax",
            "monthly",
            "--month",
            "2025-10",
            "--export",
            "csv",
            "--output",
            str(export_path),
        ],
    )

    assert export_result.exit_code == 0, export_result.stdout
    assert export_path.exists()

    with export_path.open() as f:
        rows = list(csv.reader(f))
    assert ["metric", "value"] == rows[0]
    assert any(row[0] == "taxable_base" and row[1] == "5000" for row in rows)
