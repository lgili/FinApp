"""Tests for GenerateBalanceSheetReportUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
import pytest

from finlite.application.use_cases.generate_balance_sheet_report import (
    BalanceSheetReport,
    BalanceSheetAccountRow,
    GenerateBalanceSheetCommand,
    GenerateBalanceSheetReportUseCase,
    ComparisonMode,
)
from finlite.domain.entities.account import Account
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting


class TestGenerateBalanceSheetReportUseCase:
    """Unit tests for the balance sheet report use case."""

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
    ) -> GenerateBalanceSheetReportUseCase:
        """Construct the use case with mocked dependencies."""
        return GenerateBalanceSheetReportUseCase(
            uow=mock_uow,
            account_repository=mock_account_repository,
            transaction_repository=mock_transaction_repository,
        )

    def test_no_accounts_returns_zero_totals(
        self,
        use_case: GenerateBalanceSheetReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """When no accounts exist, the report should return zero totals."""
        mock_account_repository.list_all.return_value = []
        mock_transaction_repository.find_by_date_range.return_value = []

        result = use_case.execute(
            GenerateBalanceSheetCommand(as_of=date(2025, 10, 31), currency="USD")
        )

        assert isinstance(result, BalanceSheetReport)
        assert result.assets_total == Decimal("0")
        assert result.liabilities_total == Decimal("0")
        assert result.equity_total == Decimal("0")
        assert result.net_worth == Decimal("0")
        assert result.assets == []
        assert result.liabilities == []
        assert result.equity == []

    def test_aggregates_assets_liabilities_and_equity(
        self,
        use_case: GenerateBalanceSheetReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Balances are aggregated by account type with normalized totals."""
        asset_account = Account.create(
            code="Assets:Bank:Checking",
            name="Checking",
            account_type=AccountType.ASSET,
            currency="USD",
        )
        liability_account = Account.create(
            code="Liabilities:CreditCard",
            name="Credit Card",
            account_type=AccountType.LIABILITY,
            currency="USD",
        )
        equity_account = Account.create(
            code="Equity:OpeningBalances",
            name="Opening Balances",
            account_type=AccountType.EQUITY,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [
            asset_account,
            liability_account,
            equity_account,
        ]

        opening_tx = Transaction.create(
            date=date(2025, 1, 1),
            description="Opening balance",
            postings=[
                Posting(asset_account.id, Money.from_float(5000.0, "USD")),
                Posting(equity_account.id, Money.from_float(-5000.0, "USD")),
            ],
        )
        loan_tx = Transaction.create(
            date=date(2025, 1, 10),
            description="Loan proceeds",
            postings=[
                Posting(asset_account.id, Money.from_float(2000.0, "USD")),
                Posting(liability_account.id, Money.from_float(-2000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [
            opening_tx,
            loan_tx,
        ]

        result = use_case.execute(
            GenerateBalanceSheetCommand(as_of=date(2025, 1, 31), currency="USD")
        )

        assert result.assets_total == Decimal("7000.0")
        assert result.liabilities_total == Decimal("2000.0")
        assert result.equity_total == Decimal("5000.0")
        assert result.net_worth == Decimal("5000.0")

        assert len(result.assets) == 1
        asset_row = result.assets[0]
        assert isinstance(asset_row, BalanceSheetAccountRow)
        assert asset_row.account_code == "Assets:Bank:Checking"
        assert asset_row.balance == Decimal("7000.0")
        assert asset_row.transaction_count == 2

        assert len(result.liabilities) == 1
        assert result.liabilities[0].balance == Decimal("2000.0")

        assert len(result.equity) == 1
        assert result.equity[0].balance == Decimal("5000.0")

    def test_filters_transactions_after_effective_date(
        self,
        use_case: GenerateBalanceSheetReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Transactions occurring after the as-of date are ignored."""
        asset_account = Account.create(
            code="Assets:Cash",
            name="Cash",
            account_type=AccountType.ASSET,
            currency="USD",
        )
        equity_account = Account.create(
            code="Equity:Capital",
            name="Capital",
            account_type=AccountType.EQUITY,
            currency="USD",
        )
        liability_account = Account.create(
            code="Liabilities:Loan",
            name="Loan",
            account_type=AccountType.LIABILITY,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [
            asset_account,
            equity_account,
            liability_account,
        ]

        initial_tx = Transaction.create(
            date=date(2025, 1, 5),
            description="Initial capital",
            postings=[
                Posting(asset_account.id, Money.from_float(3000.0, "USD")),
                Posting(equity_account.id, Money.from_float(-3000.0, "USD")),
            ],
        )
        later_tx = Transaction.create(
            date=date(2025, 2, 15),
            description="Loan draw",
            postings=[
                Posting(asset_account.id, Money.from_float(1000.0, "USD")),
                Posting(liability_account.id, Money.from_float(-1000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [
            initial_tx,
            later_tx,
        ]

        command = GenerateBalanceSheetCommand(as_of=date(2025, 1, 31), currency="USD")
        result = use_case.execute(command)

        mock_transaction_repository.find_by_date_range.assert_called_once_with(
            start_date=date(1900, 1, 1),
            end_date=date(2025, 1, 31),
        )

        assert result.assets_total == Decimal("3000.0")
        assert result.liabilities_total == Decimal("0")
        assert result.net_worth == Decimal("3000.0")
        assert len(result.liabilities) == 0

    def test_previous_month_comparison(
        self,
        use_case: GenerateBalanceSheetReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Previous month comparison calculates deltas correctly."""
        asset_account = Account.create(
            code="Assets:Bank",
            name="Bank",
            account_type=AccountType.ASSET,
            currency="USD",
        )
        equity_account = Account.create(
            code="Equity:Capital",
            name="Capital",
            account_type=AccountType.EQUITY,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [asset_account, equity_account]

        # Initial transaction (included in both periods)
        initial_tx = Transaction.create(
            date=date(2025, 9, 1),
            description="Initial",
            postings=[
                Posting(asset_account.id, Money.from_float(1000.0, "USD")),
                Posting(equity_account.id, Money.from_float(-1000.0, "USD")),
            ],
        )
        # Growth transaction (only in current period)
        growth_tx = Transaction.create(
            date=date(2025, 10, 15),
            description="Growth",
            postings=[
                Posting(asset_account.id, Money.from_float(500.0, "USD")),
                Posting(equity_account.id, Money.from_float(-500.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [
            initial_tx,
            growth_tx,
        ]

        command = GenerateBalanceSheetCommand(
            as_of=date(2025, 10, 31),
            currency="USD",
            comparison_mode=ComparisonMode.PREVIOUS_MONTH,
        )
        result = use_case.execute(command)

        # Current totals (both transactions)
        assert result.assets_total == Decimal("1500.0")
        assert result.equity_total == Decimal("1500.0")

        # Comparison totals (only initial transaction)
        assert result.comparison_assets_total == Decimal("1000.0")
        assert result.comparison_equity_total == Decimal("1000.0")

        # Check account row has comparison data
        assert len(result.assets) == 1
        asset_row = result.assets[0]
        assert asset_row.balance == Decimal("1500.0")
        assert asset_row.comparison_balance == Decimal("1000.0")
        assert asset_row.change_amount == Decimal("500.0")
        assert asset_row.change_percent == Decimal("50.0")

    def test_custom_date_comparison(
        self,
        use_case: GenerateBalanceSheetReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """Custom date comparison works correctly."""
        asset_account = Account.create(
            code="Assets:Cash",
            name="Cash",
            account_type=AccountType.ASSET,
            currency="USD",
        )
        equity_account = Account.create(
            code="Equity:Capital",
            name="Capital",
            account_type=AccountType.EQUITY,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [asset_account, equity_account]

        tx1 = Transaction.create(
            date=date(2025, 1, 1),
            description="Initial",
            postings=[
                Posting(asset_account.id, Money.from_float(1000.0, "USD")),
                Posting(equity_account.id, Money.from_float(-1000.0, "USD")),
            ],
        )
        tx2 = Transaction.create(
            date=date(2025, 6, 1),
            description="Midyear",
            postings=[
                Posting(asset_account.id, Money.from_float(2000.0, "USD")),
                Posting(equity_account.id, Money.from_float(-2000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [tx1, tx2]

        command = GenerateBalanceSheetCommand(
            as_of=date(2025, 12, 31),
            currency="USD",
            comparison_mode=ComparisonMode.CUSTOM_DATE,
            comparison_date=date(2025, 3, 31),
        )
        result = use_case.execute(command)

        assert result.comparison_date == date(2025, 3, 31)
        assert result.assets_total == Decimal("3000.0")
        assert result.comparison_assets_total == Decimal("1000.0")

    def test_no_comparison_when_mode_none(
        self,
        use_case: GenerateBalanceSheetReportUseCase,
        mock_account_repository: Mock,
        mock_transaction_repository: Mock,
    ) -> None:
        """No comparison data is calculated when mode is NONE."""
        asset_account = Account.create(
            code="Assets:Cash",
            name="Cash",
            account_type=AccountType.ASSET,
            currency="USD",
        )
        equity_account = Account.create(
            code="Equity:Capital",
            name="Capital",
            account_type=AccountType.EQUITY,
            currency="USD",
        )

        mock_account_repository.list_all.return_value = [asset_account, equity_account]

        tx = Transaction.create(
            date=date(2025, 10, 1),
            description="Transaction",
            postings=[
                Posting(asset_account.id, Money.from_float(1000.0, "USD")),
                Posting(equity_account.id, Money.from_float(-1000.0, "USD")),
            ],
        )

        mock_transaction_repository.find_by_date_range.return_value = [tx]

        command = GenerateBalanceSheetCommand(
            as_of=date(2025, 10, 31),
            currency="USD",
            comparison_mode=ComparisonMode.NONE,
        )
        result = use_case.execute(command)

        assert result.comparison_date is None
        assert result.comparison_assets_total is None
        assert result.comparison_liabilities_total is None
        assert result.comparison_equity_total is None
        assert result.comparison_net_worth is None

        # Check account rows have no comparison data
        assert len(result.assets) == 1
        assert result.assets[0].comparison_balance is None
        assert result.assets[0].change_amount is None
        assert result.assets[0].change_percent is None
