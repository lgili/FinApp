"""Tests for GenerateIncomeStatementReportUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
import pytest

from finlite.application.use_cases.generate_income_statement_report import (
    ComparisonMode,
    GenerateIncomeStatementCommand,
    GenerateIncomeStatementReportUseCase,
    IncomeStatementAccountRow,
    IncomeStatementReport,
)
from finlite.domain.entities.account import Account
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting


class TestGenerateIncomeStatementReportUseCase:
    """Unit tests for the income statement report use case."""

    @pytest.fixture
    def mock_uow(self) -> Mock:
        """Provide a mock unit of work with context manager support."""
        uow = Mock()
        uow.__enter__ = Mock(return_value=uow)
        uow.__exit__ = Mock(return_value=False)
        return uow

    @pytest.fixture
    def mock_account_repository(self) -> Mock:
        """Provide a mock account repository."""
        return Mock()

    @pytest.fixture
    def mock_transaction_repository(self) -> Mock:
        """Provide a mock transaction repository."""
        return Mock()

    @pytest.fixture
    def use_case(
        self,
        mock_uow: Mock,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> GenerateIncomeStatementReportUseCase:
        """Construct the use case with mocked dependencies."""
        return GenerateIncomeStatementReportUseCase(
            uow=mock_uow,
            account_repository=mock_account_repository,
            transaction_repository=mock_transaction_repository,
        )

    def test_no_accounts_returns_zero_totals(
        self,
        use_case: GenerateIncomeStatementReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """When no accounts exist, the report should return zero totals."""
        mock_account_repository.list_all.return_value = []
        mock_transaction_repository.find_by_date_range.return_value = []

        result = use_case.execute(
            GenerateIncomeStatementCommand(
                from_date=date(2025, 10, 1),
                to_date=date(2025, 10, 31),
                currency="USD",
            )
        )

        assert isinstance(result, IncomeStatementReport)
        assert result.revenue_total == Decimal("0")
        assert result.expenses_total == Decimal("0")
        assert result.net_income == Decimal("0")
        assert result.revenue == []
        assert result.expenses == []

    def test_aggregates_revenue_and_expenses(
        self,
        use_case: GenerateIncomeStatementReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Revenue and expenses are aggregated correctly with positive amounts."""
        income_account = Account.create(
            code="Income:Salary",
            name="Salary",
            account_type=AccountType.INCOME,
            currency="USD",
        )
        expense_account = Account.create(
            code="Expenses:Rent",
            name="Rent",
            account_type=AccountType.EXPENSE,
            currency="USD",
        )
        asset_account = Account.create(
            code="Assets:Bank",
            name="Bank",
            account_type=AccountType.ASSET,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [
            income_account,
            expense_account,
            asset_account,
        ]

        # Salary payment (debit asset, credit income)
        salary_tx = Transaction.create(
            date=date(2025, 10, 15),
            description="Salary payment",
            postings=[
                Posting(asset_account.id, Money.from_float(5000.0, "USD")),
                Posting(income_account.id, Money.from_float(-5000.0, "USD")),
            ],
        )

        # Rent payment (credit asset, debit expense)
        rent_tx = Transaction.create(
            date=date(2025, 10, 1),
            description="Rent payment",
            postings=[
                Posting(expense_account.id, Money.from_float(1500.0, "USD")),
                Posting(asset_account.id, Money.from_float(-1500.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [
            salary_tx,
            rent_tx,
        ]

        result = use_case.execute(
            GenerateIncomeStatementCommand(
                from_date=date(2025, 10, 1),
                to_date=date(2025, 10, 31),
                currency="USD",
            )
        )

        # Revenue should be positive (income credits shown as positive)
        assert result.revenue_total == Decimal("5000.0")
        # Expenses should be positive (expense debits shown as positive)
        assert result.expenses_total == Decimal("1500.0")
        # Net income = revenue - expenses
        assert result.net_income == Decimal("3500.0")

        assert len(result.revenue) == 1
        revenue_row = result.revenue[0]
        assert isinstance(revenue_row, IncomeStatementAccountRow)
        assert revenue_row.account_code == "Income:Salary"
        assert revenue_row.amount == Decimal("5000.0")
        assert revenue_row.transaction_count == 1

        assert len(result.expenses) == 1
        expense_row = result.expenses[0]
        assert expense_row.account_code == "Expenses:Rent"
        assert expense_row.amount == Decimal("1500.0")
        assert expense_row.transaction_count == 1

    def test_filters_transactions_by_date_range(
        self,
        use_case: GenerateIncomeStatementReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Only transactions within the date range are included."""
        income_account = Account.create(
            code="Income:Sales",
            name="Sales",
            account_type=AccountType.INCOME,
            currency="USD",
        )
        asset_account = Account.create(
            code="Assets:Cash",
            name="Cash",
            account_type=AccountType.ASSET,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [income_account, asset_account]

        # Transaction before period
        early_tx = Transaction.create(
            date=date(2025, 9, 15),
            description="September sale",
            postings=[
                Posting(asset_account.id, Money.from_float(1000.0, "USD")),
                Posting(income_account.id, Money.from_float(-1000.0, "USD")),
            ],
        )

        # Transaction in period
        current_tx = Transaction.create(
            date=date(2025, 10, 15),
            description="October sale",
            postings=[
                Posting(asset_account.id, Money.from_float(2000.0, "USD")),
                Posting(income_account.id, Money.from_float(-2000.0, "USD")),
            ],
        )

        # Transaction after period
        late_tx = Transaction.create(
            date=date(2025, 11, 15),
            description="November sale",
            postings=[
                Posting(asset_account.id, Money.from_float(1500.0, "USD")),
                Posting(income_account.id, Money.from_float(-1500.0, "USD")),
            ],
        )

        # Repository returns only transactions in the requested range
        mock_transaction_repository.find_by_date_range.return_value = [current_tx]

        result = use_case.execute(
            GenerateIncomeStatementCommand(
                from_date=date(2025, 10, 1),
                to_date=date(2025, 10, 31),
                currency="USD",
            )
        )

        # Verify the repository was called with the correct date range
        mock_transaction_repository.find_by_date_range.assert_any_call(
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31),
        )

        # Only October transaction should be included
        assert result.revenue_total == Decimal("2000.0")

    def test_comparison_mode_previous_period(
        self,
        use_case: GenerateIncomeStatementReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Comparison mode PREVIOUS_PERIOD compares to the immediately preceding period."""
        income_account = Account.create(
            code="Income:Sales",
            name="Sales",
            account_type=AccountType.INCOME,
            currency="USD",
        )
        asset_account = Account.create(
            code="Assets:Cash",
            name="Cash",
            account_type=AccountType.ASSET,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [income_account, asset_account]

        # Current period transaction (Oct 1-31)
        current_tx = Transaction.create(
            date=date(2025, 10, 15),
            description="October sale",
            postings=[
                Posting(asset_account.id, Money.from_float(3000.0, "USD")),
                Posting(income_account.id, Money.from_float(-3000.0, "USD")),
            ],
        )

        # Previous period transaction (Sep 1-30)
        previous_tx = Transaction.create(
            date=date(2025, 9, 15),
            description="September sale",
            postings=[
                Posting(asset_account.id, Money.from_float(2000.0, "USD")),
                Posting(income_account.id, Money.from_float(-2000.0, "USD")),
            ],
        )

        # Mock repository to return different data for different date ranges
        # Previous period for Oct 1-31 (31 days) is Aug 31 - Sep 30 (31 days)
        def mock_find_by_date_range(start_date, end_date):
            if start_date == date(2025, 10, 1) and end_date == date(2025, 10, 31):
                return [current_tx]
            elif start_date == date(2025, 8, 31) and end_date == date(2025, 9, 30):
                return [previous_tx]
            return []

        mock_transaction_repository.find_by_date_range.side_effect = mock_find_by_date_range

        result = use_case.execute(
            GenerateIncomeStatementCommand(
                from_date=date(2025, 10, 1),
                to_date=date(2025, 10, 31),
                currency="USD",
                comparison_mode=ComparisonMode.PREVIOUS_PERIOD,
            )
        )

        # Current period (31 days)
        assert result.revenue_total == Decimal("3000.0")
        assert result.comparison_revenue_total == Decimal("2000.0")
        # Previous period should also be 31 days: Aug 31 - Sep 30
        assert result.comparison_from_date == date(2025, 8, 31)
        assert result.comparison_to_date == date(2025, 9, 30)

        # Comparison data should be in the rows
        assert len(result.revenue) == 1
        row = result.revenue[0]
        assert row.comparison_amount == Decimal("2000.0")
        assert row.change_amount == Decimal("1000.0")
        assert row.change_percent == Decimal("50.0")

    def test_comparison_mode_year_over_year(
        self,
        use_case: GenerateIncomeStatementReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Comparison mode YEAR_OVER_YEAR compares to the same period last year."""
        income_account = Account.create(
            code="Income:Sales",
            name="Sales",
            account_type=AccountType.INCOME,
            currency="USD",
        )
        asset_account = Account.create(
            code="Assets:Cash",
            name="Cash",
            account_type=AccountType.ASSET,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [income_account, asset_account]

        # Current year transaction (Oct 2025)
        current_tx = Transaction.create(
            date=date(2025, 10, 15),
            description="2025 sale",
            postings=[
                Posting(asset_account.id, Money.from_float(4000.0, "USD")),
                Posting(income_account.id, Money.from_float(-4000.0, "USD")),
            ],
        )

        # Previous year transaction (Oct 2024)
        previous_year_tx = Transaction.create(
            date=date(2024, 10, 15),
            description="2024 sale",
            postings=[
                Posting(asset_account.id, Money.from_float(2500.0, "USD")),
                Posting(income_account.id, Money.from_float(-2500.0, "USD")),
            ],
        )

        def mock_find_by_date_range(start_date, end_date):
            if start_date == date(2025, 10, 1) and end_date == date(2025, 10, 31):
                return [current_tx]
            elif start_date == date(2024, 10, 1) and end_date == date(2024, 10, 31):
                return [previous_year_tx]
            return []

        mock_transaction_repository.find_by_date_range.side_effect = mock_find_by_date_range

        result = use_case.execute(
            GenerateIncomeStatementCommand(
                from_date=date(2025, 10, 1),
                to_date=date(2025, 10, 31),
                currency="USD",
                comparison_mode=ComparisonMode.YEAR_OVER_YEAR,
            )
        )

        assert result.revenue_total == Decimal("4000.0")
        assert result.comparison_revenue_total == Decimal("2500.0")
        assert result.comparison_from_date == date(2024, 10, 1)
        assert result.comparison_to_date == date(2024, 10, 31)

        # YoY growth should be calculated
        assert len(result.revenue) == 1
        row = result.revenue[0]
        assert row.comparison_amount == Decimal("2500.0")
        assert row.change_amount == Decimal("1500.0")
        assert row.change_percent == Decimal("60.0")

    def test_net_income_calculation(
        self,
        use_case: GenerateIncomeStatementReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Net income is calculated correctly as revenue - expenses."""
        income_account = Account.create(
            code="Income:Service",
            name="Service Revenue",
            account_type=AccountType.INCOME,
            currency="USD",
        )
        expense_account1 = Account.create(
            code="Expenses:Salary",
            name="Salaries",
            account_type=AccountType.EXPENSE,
            currency="USD",
        )
        expense_account2 = Account.create(
            code="Expenses:Office",
            name="Office Rent",
            account_type=AccountType.EXPENSE,
            currency="USD",
        )
        asset_account = Account.create(
            code="Assets:Bank",
            name="Bank",
            account_type=AccountType.ASSET,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [
            income_account,
            expense_account1,
            expense_account2,
            asset_account,
        ]

        revenue_tx = Transaction.create(
            date=date(2025, 10, 15),
            description="Service income",
            postings=[
                Posting(asset_account.id, Money.from_float(10000.0, "USD")),
                Posting(income_account.id, Money.from_float(-10000.0, "USD")),
            ],
        )

        salary_tx = Transaction.create(
            date=date(2025, 10, 20),
            description="Salary payment",
            postings=[
                Posting(expense_account1.id, Money.from_float(6000.0, "USD")),
                Posting(asset_account.id, Money.from_float(-6000.0, "USD")),
            ],
        )

        rent_tx = Transaction.create(
            date=date(2025, 10, 5),
            description="Office rent",
            postings=[
                Posting(expense_account2.id, Money.from_float(2000.0, "USD")),
                Posting(asset_account.id, Money.from_float(-2000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [
            revenue_tx,
            salary_tx,
            rent_tx,
        ]

        result = use_case.execute(
            GenerateIncomeStatementCommand(
                from_date=date(2025, 10, 1),
                to_date=date(2025, 10, 31),
                currency="USD",
            )
        )

        assert result.revenue_total == Decimal("10000.0")
        assert result.expenses_total == Decimal("8000.0")  # 6000 + 2000
        assert result.net_income == Decimal("2000.0")  # 10000 - 8000

        # Check that expenses are sorted by amount (descending)
        assert len(result.expenses) == 2
        assert result.expenses[0].amount >= result.expenses[1].amount

    def test_filters_by_currency(
        self,
        use_case: GenerateIncomeStatementReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Only accounts and transactions matching the currency are included."""
        usd_income = Account.create(
            code="Income:USD",
            name="USD Income",
            account_type=AccountType.INCOME,
            currency="USD",
        )
        brl_income = Account.create(
            code="Income:BRL",
            name="BRL Income",
            account_type=AccountType.INCOME,
            currency="BRL",
        )
        usd_asset = Account.create(
            code="Assets:USD",
            name="USD Bank",
            account_type=AccountType.ASSET,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [
            usd_income,
            brl_income,
            usd_asset,
        ]

        # USD transaction
        usd_tx = Transaction.create(
            date=date(2025, 10, 15),
            description="USD income",
            postings=[
                Posting(usd_asset.id, Money.from_float(1000.0, "USD")),
                Posting(usd_income.id, Money.from_float(-1000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [usd_tx]

        result = use_case.execute(
            GenerateIncomeStatementCommand(
                from_date=date(2025, 10, 1),
                to_date=date(2025, 10, 31),
                currency="USD",
            )
        )

        # Only USD income should be included
        assert result.revenue_total == Decimal("1000.0")
        assert len(result.revenue) == 1
        assert result.revenue[0].account_code == "Income:USD"
