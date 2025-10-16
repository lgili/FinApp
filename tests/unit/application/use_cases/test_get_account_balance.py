"""Unit tests for GetAccountBalanceUseCase."""

from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
import pytest

from finlite.application.use_cases import GetAccountBalanceUseCase
from finlite.domain.entities import Account
from finlite.domain.exceptions import AccountNotFoundError
from finlite.domain.value_objects import AccountType


class TestGetAccountBalanceUseCase:
    """Test suite for GetAccountBalanceUseCase."""

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = Mock()
        uow.__enter__ = Mock(return_value=uow)
        uow.__exit__ = Mock(return_value=False)
        return uow

    @pytest.fixture
    def use_case(self, mock_uow):
        """Create use case instance."""
        return GetAccountBalanceUseCase(uow=mock_uow)

    @pytest.fixture
    def sample_account(self):
        """Create a sample account."""
        return Account(
            id=uuid4(),
            code="Assets:Checking",
            name="Checking Account",
            account_type=AccountType.ASSET,
            currency="USD",
            is_active=True,
        )

    def test_get_account_balance_by_code_success(
        self, use_case, mock_uow, sample_account
    ):
        """Test successfully getting account balance by code."""
        # Arrange
        mock_uow.accounts.find_by_code.return_value = sample_account
        mock_uow.transactions.find_by_date_range.return_value = []  # No transactions

        # Act
        result = use_case.execute_by_code("Assets:Checking")

        # Assert
        assert result.code == "Assets:Checking"
        assert result.name == "Checking Account"
        assert result.type == "ASSET"
        assert result.currency == "USD"
        assert isinstance(result.balance, Decimal)
        assert result.balance == Decimal("0")  # No transactions
        mock_uow.accounts.find_by_code.assert_called_once_with("Assets:Checking")

    def test_get_account_balance_by_code_not_found(self, use_case, mock_uow):
        """Test getting balance for non-existent account by code."""
        # Arrange
        mock_uow.accounts.find_by_code.return_value = None

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc_info:
            use_case.execute_by_code("NonExistent:Account")

        assert "NonExistent:Account" in str(exc_info.value)
        mock_uow.accounts.find_by_code.assert_called_once_with("NonExistent:Account")

    def test_get_account_balance_by_id_success(
        self, use_case, mock_uow, sample_account
    ):
        """Test successfully getting account balance by ID."""
        # Arrange
        account_id = sample_account.id
        mock_uow.accounts.get.return_value = sample_account
        mock_uow.transactions.find_by_date_range.return_value = []  # No transactions

        # Act
        result = use_case.execute_by_id(account_id)

        # Assert
        assert result.id == account_id
        assert result.code == "Assets:Checking"
        assert result.type == "ASSET"
        assert result.currency == "USD"
        assert result.balance == Decimal("0")  # No transactions = 0 balance
        mock_uow.accounts.get.assert_called_once_with(account_id)

    def test_get_account_balance_dto_structure(
        self, use_case, mock_uow, sample_account
    ):
        """Test that returned DTO has correct structure."""
        # Arrange
        mock_uow.accounts.find_by_code.return_value = sample_account
        mock_uow.transactions.find_by_date_range.return_value = []  # No transactions

        # Act
        result = use_case.execute_by_code("Assets:Checking")

        # Assert
        assert hasattr(result, "id")
        assert hasattr(result, "code")
        assert hasattr(result, "name")
        assert hasattr(result, "type")
        assert hasattr(result, "currency")
        assert hasattr(result, "balance")
        assert hasattr(result, "parent_code")
        assert hasattr(result, "is_placeholder")
        assert hasattr(result, "tags")

    def test_get_different_account_types(self, use_case, mock_uow):
        """Test getting balances for different account types."""
        account_types = [
            ("Assets:Bank", AccountType.ASSET),
            ("Expenses:Food", AccountType.EXPENSE),
            ("Income:Salary", AccountType.INCOME),
            ("Liabilities:Loan", AccountType.LIABILITY),
            ("Equity:Capital", AccountType.EQUITY),
        ]

        for code, acc_type in account_types:
            account = Account(
                id=uuid4(),
                code=code,
                name=f"{code} Account",
                account_type=acc_type,
                currency="BRL",
                is_active=True,
            )
            mock_uow.accounts.find_by_code.return_value = account
            mock_uow.transactions.find_by_date_range.return_value = []  # No transactions

            # Act
            result = use_case.execute_by_code(code)

            # Assert
            assert result.code == code
            assert result.type == acc_type.name
            assert result.currency == "BRL"

    def test_get_account_balance_different_currencies(self, use_case, mock_uow):
        """Test getting balances for accounts with different currencies."""
        currencies = ["USD", "BRL", "EUR", "GBP"]

        for currency in currencies:
            account = Account(
                id=uuid4(),
                code=f"Assets:{currency}Account",
                name=f"{currency} Account",
                account_type=AccountType.ASSET,
                currency=currency,
                is_active=True,
            )
            mock_uow.accounts.find_by_code.return_value = account
            mock_uow.transactions.find_by_date_range.return_value = []  # No transactions

            # Act
            result = use_case.execute_by_code(f"Assets:{currency}Account")

            # Assert
            assert result.currency == currency
