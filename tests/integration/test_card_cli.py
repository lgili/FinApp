"""Integration tests for credit card CLI flows."""

from datetime import date
from decimal import Decimal
import importlib

from typer.testing import CliRunner

from finlite.application.dtos import (
    CreateAccountDTO,
    CreatePostingDTO,
    CreateTransactionDTO,
)
from finlite.application.use_cases.record_transaction import RecordTransactionUseCase
from finlite.shared.di import create_container, init_database


def setup_accounts(container) -> None:
    create_account = container.create_account_use_case()
    create_account.execute(
        CreateAccountDTO(
            code="Liabilities:CreditCard:Nubank",
            name="Nubank",
            type="LIABILITY",
            currency="BRL",
            card_issuer="Nubank",
            card_closing_day=7,
            card_due_day=15,
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Expenses:Groceries",
            name="Groceries",
            type="EXPENSE",
            currency="BRL",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Assets:Checking",
            name="Checking",
            type="ASSET",
            currency="BRL",
        )
    )


def record_purchase(
    container,
    amount: Decimal,
    description: str,
    tags: tuple[str, ...],
    occurred_at: date,
) -> None:
    record_use_case: RecordTransactionUseCase = container.record_transaction_use_case()
    record_use_case.execute(
        CreateTransactionDTO(
            date=occurred_at,
            description=description,
            postings=(
                CreatePostingDTO("Expenses:Groceries", amount, "BRL"),
                CreatePostingDTO("Liabilities:CreditCard:Nubank", -amount, "BRL"),
            ),
            tags=tags,
        )
    )


def test_card_build_statement_cli(tmp_path, monkeypatch):
    db_path = tmp_path / "card.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)
    setup_accounts(container)

    record_purchase(
        container,
        amount=Decimal("120.00"),
        description="Supermarket",
        tags=("card:installment=1/3", "card:installment_key=SUPERMARKET-001"),
        occurred_at=date(2025, 9, 20),
    )
    record_purchase(
        container,
        amount=Decimal("80.00"),
        description="Drugstore",
        tags=(),
        occurred_at=date(2025, 10, 5),
    )

    cli_app_module = importlib.import_module("finlite.interfaces.cli.app")
    monkeypatch.setattr(cli_app_module, "_container", container, raising=False)

    runner = CliRunner()
    result = runner.invoke(
        cli_app_module.app,
        ["card", "build-statement", "--card", "Liabilities:CreditCard:Nubank", "--period", "2025-10"],
    )

    assert result.exit_code == 0, result.stdout
    assert "Total Due" in result.stdout
    assert "Nubank" in result.stdout
    assert "Installment" in result.stdout

    list_result = runner.invoke(cli_app_module.app, ["card", "list"])
    assert list_result.exit_code == 0
    assert "Nubank" in list_result.stdout
