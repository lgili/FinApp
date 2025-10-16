"""Tests for GenerateCashflowReportUseCase."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from finlite.application.use_cases.generate_cashflow_report import (
    CashflowReport,
    GenerateCashflowCommand,
    GenerateCashflowReportUseCase,
)
from finlite.domain.entities.account import Account
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting


class TestGenerateCashflowReportUseCase:
    """Tests for GenerateCashflowReportUseCase."""

    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work."""
        uow = Mock()
        uow.__enter__ = Mock(return_value=uow)
        uow.__exit__ = Mock(return_value=False)
        return uow

    @pytest.fixture
    def mock_account_repository(self):
        """Mock Account Repository."""
        return Mock()

    @pytest.fixture
    def mock_transaction_repository(self):
        """Mock Transaction Repository."""
        return Mock()

    @pytest.fixture
    def use_case(
        self, mock_uow, mock_account_repository, mock_transaction_repository
    ):
        """Create use case instance."""
        return GenerateCashflowReportUseCase(
            uow=mock_uow,
            account_repository=mock_account_repository,
            transaction_repository=mock_transaction_repository,
        )

    @pytest.fixture
    def checking_account(self):
        """Create checking account."""
        return Account.create(
            code="Assets:Bank:Checking",
            name="Checking Account",
            account_type=AccountType.ASSET,
            currency="USD",
        )

    @pytest.fixture
    def salary_account(self):
        """Create salary income account."""
        return Account.create(
            code="Income:Salary",
            name="Salary",
            account_type=AccountType.INCOME,
            currency="USD",
        )

    @pytest.fixture
    def groceries_account(self):
        """Create groceries expense account."""
        return Account.create(
            code="Expenses:Groceries",
            name="Groceries",
            account_type=AccountType.EXPENSE,
            currency="USD",
        )

    def test_empty_period_returns_zero_report(
        self, use_case, mock_transaction_repository, mock_account_repository
    ):
        """When no transactions exist in period, return zero report."""
        mock_transaction_repository.find_by_date_range.return_value = []
        mock_account_repository.list_all.return_value = []

        result = use_case.execute(
            GenerateCashflowCommand(
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
                currency="USD",
            )
        )

        assert isinstance(result, CashflowReport)
        assert result.total_income == Decimal("0")
        assert result.total_expenses == Decimal("0")
        assert result.net_cashflow == Decimal("0")
        assert len(result.income_categories) == 0
        assert len(result.expense_categories) == 0

    def test_single_income_transaction(
        self,
        use_case,
        mock_transaction_repository,
        mock_account_repository,
        checking_account,
        salary_account,
    ):
        """Successfully processes single income transaction."""
        # Create salary transaction
        transaction = Transaction.create(
            date=datetime(2025, 10, 1).date(),
            description="Monthly Salary",
            postings=[
                Posting(checking_account.id, Money.from_float(5000.0, "USD")),
                Posting(salary_account.id, Money.from_float(-5000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [transaction]
        mock_account_repository.list_all.return_value = [
            checking_account,
            salary_account,
        ]

        result = use_case.execute(
            GenerateCashflowCommand(
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
                currency="USD",
            )
        )

        assert result.total_income == Decimal("5000.0")
        assert result.total_expenses == Decimal("0")
        assert result.net_cashflow == Decimal("5000.0")
        assert len(result.income_categories) == 1
        assert result.income_categories[0].account_code == "Income:Salary"
        assert abs(result.income_categories[0].amount) == Decimal("5000.0")

    def test_single_expense_transaction(
        self,
        use_case,
        mock_transaction_repository,
        mock_account_repository,
        checking_account,
        groceries_account,
    ):
        """Successfully processes single expense transaction."""
        transaction = Transaction.create(
            date=datetime(2025, 10, 12).date(),
            description="Grocery shopping",
            postings=[
                Posting(checking_account.id, Money.from_float(-150.0, "USD")),
                Posting(groceries_account.id, Money.from_float(150.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [transaction]
        mock_account_repository.list_all.return_value = [
            checking_account,
            groceries_account,
        ]

        result = use_case.execute(
            GenerateCashflowCommand(
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
                currency="USD",
            )
        )

        assert result.total_income == Decimal("0")
        assert result.total_expenses == Decimal("150.0")
        assert result.net_cashflow == Decimal("-150.0")
        assert len(result.expense_categories) == 1
        assert result.expense_categories[0].account_code == "Expenses:Groceries"

    def test_mixed_income_and_expenses(
        self,
        use_case,
        mock_transaction_repository,
        mock_account_repository,
        checking_account,
        salary_account,
        groceries_account,
    ):
        """Successfully processes mix of income and expense transactions."""
        # Income transaction
        income_tx = Transaction.create(
            date=datetime(2025, 10, 1).date(),
            description="Salary",
            postings=[
                Posting(checking_account.id, Money.from_float(5000.0, "USD")),
                Posting(salary_account.id, Money.from_float(-5000.0, "USD")),
            ],
        )

        # Expense transaction
        expense_tx = Transaction.create(
            date=datetime(2025, 10, 12).date(),
            description="Groceries",
            postings=[
                Posting(checking_account.id, Money.from_float(-150.0, "USD")),
                Posting(groceries_account.id, Money.from_float(150.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [
            income_tx,
            expense_tx,
        ]
        mock_account_repository.list_all.return_value = [
            checking_account,
            salary_account,
            groceries_account,
        ]

        result = use_case.execute(
            GenerateCashflowCommand(
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
                currency="USD",
            )
        )

        assert result.total_income == Decimal("5000.0")
        assert result.total_expenses == Decimal("150.0")
        assert result.net_cashflow == Decimal("4850.0")
        assert len(result.income_categories) == 1
        assert len(result.expense_categories) == 1

    def test_aggregates_multiple_transactions_same_account(
        self,
        use_case,
        mock_transaction_repository,
        mock_account_repository,
        checking_account,
        groceries_account,
    ):
        """Aggregates multiple transactions for same account."""
        tx1 = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Groceries 1",
            postings=[
                Posting(checking_account.id, Money.from_float(-100.0, "USD")),
                Posting(groceries_account.id, Money.from_float(100.0, "USD")),
            ],
        )

        tx2 = Transaction.create(
            date=datetime(2025, 10, 15).date(),
            description="Groceries 2",
            postings=[
                Posting(checking_account.id, Money.from_float(-50.0, "USD")),
                Posting(groceries_account.id, Money.from_float(50.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [tx1, tx2]
        mock_account_repository.list_all.return_value = [
            checking_account,
            groceries_account,
        ]

        result = use_case.execute(
            GenerateCashflowCommand(
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
                currency="USD",
            )
        )

        assert result.total_expenses == Decimal("150.0")
        assert len(result.expense_categories) == 1
        assert result.expense_categories[0].transaction_count == 2

    def test_filter_by_account_code_prefix(
        self,
        use_case,
        mock_transaction_repository,
        mock_account_repository,
        checking_account,
        groceries_account,
    ):
        """Filters results by account code prefix."""
        rent_account = Account.create(
            code="Expenses:Rent",
            name="Rent",
            account_type=AccountType.EXPENSE,
            currency="USD",
        )

        tx1 = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Groceries",
            postings=[
                Posting(checking_account.id, Money.from_float(-100.0, "USD")),
                Posting(groceries_account.id, Money.from_float(100.0, "USD")),
            ],
        )

        tx2 = Transaction.create(
            date=datetime(2025, 10, 10).date(),
            description="Rent payment",
            postings=[
                Posting(checking_account.id, Money.from_float(-1000.0, "USD")),
                Posting(rent_account.id, Money.from_float(1000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [tx1, tx2]
        mock_account_repository.list_all.return_value = [
            checking_account,
            groceries_account,
            rent_account,
        ]

        # Filter only Expenses:Groceries
        result = use_case.execute(
            GenerateCashflowCommand(
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
                currency="USD",
                account_code_filter="Expenses:Groceries",
            )
        )

        assert result.total_expenses == Decimal("100.0")
        assert len(result.expense_categories) == 1
        assert result.expense_categories[0].account_code == "Expenses:Groceries"

    def test_skips_different_currencies(
        self,
        use_case,
        mock_transaction_repository,
        mock_account_repository,
        checking_account,
    ):
        """Skips transactions in different currencies."""
        brl_account = Account.create(
            code="Expenses:BRL",
            name="BRL Expense",
            account_type=AccountType.EXPENSE,
            currency="BRL",
        )

        tx = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="BRL purchase",
            postings=[
                Posting(checking_account.id, Money.from_float(-100.0, "BRL")),
                Posting(brl_account.id, Money.from_float(100.0, "BRL")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [tx]
        mock_account_repository.list_all.return_value = [
            checking_account,
            brl_account,
        ]

        # Request USD report
        result = use_case.execute(
            GenerateCashflowCommand(
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
                currency="USD",  # Different from transaction currency
            )
        )

        # Should skip BRL transaction
        assert result.total_expenses == Decimal("0")
        assert len(result.expense_categories) == 0

    def test_asset_balances_included(
        self,
        use_case,
        mock_transaction_repository,
        mock_account_repository,
        checking_account,
        salary_account,
    ):
        """Asset balances are included in the report."""
        transaction = Transaction.create(
            date=datetime(2025, 10, 1).date(),
            description="Salary",
            postings=[
                Posting(checking_account.id, Money.from_float(5000.0, "USD")),
                Posting(salary_account.id, Money.from_float(-5000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [transaction]
        mock_account_repository.list_all.return_value = [
            checking_account,
            salary_account,
        ]

        result = use_case.execute(
            GenerateCashflowCommand(
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
                currency="USD",
            )
        )

        assert len(result.asset_balances) == 1
        assert result.asset_balances[0].account_code == "Assets:Bank:Checking"
        assert result.asset_balances[0].amount == Decimal("5000.0")
