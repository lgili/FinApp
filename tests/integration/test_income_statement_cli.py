"""Integration test for the income statement CLI command."""

import re
from datetime import date
from decimal import Decimal
import importlib
from pathlib import Path

from typer.testing import CliRunner

from finlite.application.dtos import CreateAccountDTO, CreatePostingDTO, CreateTransactionDTO
from finlite.shared.di import create_container, init_database

CLI_APP_MODULE = importlib.import_module("finlite.interfaces.cli.app")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text for easier assertions."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_income_statement_cli_basic(tmp_path, monkeypatch):
    """The CLI should render income statement with revenue and expenses."""
    db_path = tmp_path / "cli-income-statement.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    create_account = container.create_account_use_case()

    # Create income and expense accounts
    create_account.execute(
        CreateAccountDTO(
            code="Income:Salary",
            name="Income:Salary",
            type="INCOME",
            currency="BRL",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Expenses:Rent",
            name="Expenses:Rent",
            type="EXPENSE",
            currency="BRL",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Expenses:Food",
            name="Expenses:Food",
            type="EXPENSE",
            currency="BRL",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Assets:Bank",
            name="Assets:Bank",
            type="ASSET",
            currency="BRL",
        )
    )

    record_transaction = container.record_transaction_use_case()

    # Record salary income
    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 10, 15),
            description="Salary payment",
            postings=(
                CreatePostingDTO("Assets:Bank", Decimal("5000"), "BRL"),
                CreatePostingDTO("Income:Salary", Decimal("-5000"), "BRL"),
            ),
        )
    )

    # Record rent expense
    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 10, 1),
            description="Rent payment",
            postings=(
                CreatePostingDTO("Expenses:Rent", Decimal("1500"), "BRL"),
                CreatePostingDTO("Assets:Bank", Decimal("-1500"), "BRL"),
            ),
        )
    )

    # Record food expense
    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 10, 10),
            description="Groceries",
            postings=(
                CreatePostingDTO("Expenses:Food", Decimal("800"), "BRL"),
                CreatePostingDTO("Assets:Bank", Decimal("-800"), "BRL"),
            ),
        )
    )

    # Ensure CLI reuses this container instance
    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    runner = CliRunner()
    result = runner.invoke(
        CLI_APP_MODULE.app,
        [
            "reports",
            "income-statement",
            "--from",
            "2024-10-01",
            "--to",
            "2024-10-31",
            "--currency",
            "BRL",
        ],
    )

    assert result.exit_code == 0, result.stdout
    output = strip_ansi(result.stdout)

    # Check for revenue
    assert "Revenue" in output
    assert "5,000.00" in output  # Total revenue
    assert "Income:Salary" in output

    # Check for expenses
    assert "Expenses" in output
    assert "2,300.00" in output  # Total expenses (1500 + 800)
    assert "Expenses:Rent" in output
    assert "Expenses:Food" in output

    # Check for net income
    assert "Net Income" in output
    assert "2,700.00" in output  # Net income (5000 - 2300)


def test_income_statement_cli_export_csv(tmp_path, monkeypatch):
    """The CLI should export income statement to CSV."""
    db_path = tmp_path / "cli-income-export.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    create_account = container.create_account_use_case()

    create_account.execute(
        CreateAccountDTO(
            code="Income:Service",
            name="Income:Service",
            type="INCOME",
            currency="USD",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Expenses:Office",
            name="Expenses:Office",
            type="EXPENSE",
            currency="USD",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Assets:Cash",
            name="Assets:Cash",
            type="ASSET",
            currency="USD",
        )
    )

    record_transaction = container.record_transaction_use_case()

    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 11, 1),
            description="Service revenue",
            postings=(
                CreatePostingDTO("Assets:Cash", Decimal("3000"), "USD"),
                CreatePostingDTO("Income:Service", Decimal("-3000"), "USD"),
            ),
        )
    )

    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 11, 5),
            description="Office supplies",
            postings=(
                CreatePostingDTO("Expenses:Office", Decimal("500"), "USD"),
                CreatePostingDTO("Assets:Cash", Decimal("-500"), "USD"),
            ),
        )
    )

    # Ensure CLI reuses this container instance
    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    export_path = tmp_path / "income_statement.csv"

    runner = CliRunner()
    result = runner.invoke(
        CLI_APP_MODULE.app,
        [
            "reports",
            "income-statement",
            "--from",
            "2024-11-01",
            "--to",
            "2024-11-30",
            "--currency",
            "USD",
            "--export",
            str(export_path),
        ],
    )

    assert result.exit_code == 0, result.stdout

    # Verify the export file was created
    assert export_path.exists()

    # Read and verify CSV contents
    csv_content = export_path.read_text()
    assert "Income Statement Report" in csv_content
    assert "REVENUE" in csv_content
    assert "Income:Service" in csv_content
    assert "3000.00" in csv_content
    assert "EXPENSES" in csv_content
    assert "Expenses:Office" in csv_content
    assert "500.00" in csv_content
    assert "NET INCOME" in csv_content
    assert "2500.00" in csv_content


def test_income_statement_cli_export_markdown(tmp_path, monkeypatch):
    """The CLI should export income statement to Markdown."""
    db_path = tmp_path / "cli-income-md.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    create_account = container.create_account_use_case()

    create_account.execute(
        CreateAccountDTO(
            code="Income:Freelance",
            name="Income:Freelance",
            type="INCOME",
            currency="USD",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Expenses:Software",
            name="Expenses:Software",
            type="EXPENSE",
            currency="USD",
        )
    )
    create_account.execute(
        CreateAccountDTO(
            code="Assets:Bank",
            name="Assets:Bank",
            type="ASSET",
            currency="USD",
        )
    )

    record_transaction = container.record_transaction_use_case()

    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 12, 1),
            description="Freelance payment",
            postings=(
                CreatePostingDTO("Assets:Bank", Decimal("4000"), "USD"),
                CreatePostingDTO("Income:Freelance", Decimal("-4000"), "USD"),
            ),
        )
    )

    record_transaction.execute(
        CreateTransactionDTO(
            date=date(2024, 12, 10),
            description="Software subscription",
            postings=(
                CreatePostingDTO("Expenses:Software", Decimal("99"), "USD"),
                CreatePostingDTO("Assets:Bank", Decimal("-99"), "USD"),
            ),
        )
    )

    # Ensure CLI reuses this container instance
    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    export_path = tmp_path / "income_statement.md"

    runner = CliRunner()
    result = runner.invoke(
        CLI_APP_MODULE.app,
        [
            "reports",
            "income-statement",
            "--from",
            "2024-12-01",
            "--to",
            "2024-12-31",
            "--currency",
            "USD",
            "--export",
            str(export_path),
        ],
    )

    assert result.exit_code == 0, result.stdout

    # Verify the export file was created
    assert export_path.exists()

    # Read and verify Markdown contents
    md_content = export_path.read_text()
    assert "# Income Statement Report" in md_content
    assert "## Revenue" in md_content
    assert "Income:Freelance" in md_content
    assert "4,000.00" in md_content
    assert "## Expenses" in md_content
    assert "Expenses:Software" in md_content
    assert "99.00" in md_content
    assert "## Summary" in md_content
    assert "Net Income" in md_content
    assert "3,901.00" in md_content


def test_income_statement_cli_empty_period(tmp_path, monkeypatch):
    """The CLI should handle periods with no transactions gracefully."""
    db_path = tmp_path / "cli-income-empty.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    # Create accounts but no transactions
    create_account = container.create_account_use_case()
    create_account.execute(
        CreateAccountDTO(
            code="Income:Sales",
            name="Income:Sales",
            type="INCOME",
            currency="BRL",
        )
    )

    # Ensure CLI reuses this container instance
    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    runner = CliRunner()
    result = runner.invoke(
        CLI_APP_MODULE.app,
        [
            "reports",
            "income-statement",
            "--from",
            "2024-01-01",
            "--to",
            "2024-01-31",
            "--currency",
            "BRL",
        ],
    )

    assert result.exit_code == 0, result.stdout
    output = strip_ansi(result.stdout)

    # Should show empty state message
    assert "No income or expense data found" in output or "0.00" in output
