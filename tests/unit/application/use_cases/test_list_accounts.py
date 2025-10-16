"""Unit tests for ListAccountsUseCase."""

from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
import pytest

from finlite.application.use_cases import ListAccountsUseCase
from finlite.domain.entities import Account
from finlite.domain.value_objects import AccountType


class TestListAccountsUseCase:
    """Test suite for ListAccountsUseCase."""

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
        return ListAccountsUseCase(uow=mock_uow)

    @pytest.fixture
    def sample_accounts(self):
        """Create sample accounts for testing."""
        return [
            Account(
                id=uuid4(),
                code="Assets:Checking",
                name="Checking Account",
                account_type=AccountType.ASSET,
                currency="USD",
                is_active=True,
            ),
            Account(
                id=uuid4(),
                code="Assets:Savings",
                name="Savings Account",
                account_type=AccountType.ASSET,
                currency="USD",
                is_active=True,
            ),
            Account(
                id=uuid4(),
                code="Expenses:Food",
                name="Food Expenses",
                account_type=AccountType.EXPENSE,
                currency="USD",
                is_active=True,
            ),
            Account(
                id=uuid4(),
                code="Expenses:Transport",
                name="Transport Expenses",
                account_type=AccountType.EXPENSE,
                currency="USD",
                is_active=True,
            ),
            Account(
                id=uuid4(),
                code="Income:Salary",
                name="Salary Income",
                account_type=AccountType.INCOME,
                currency="USD",
                is_active=True,
            ),
            Account(
                id=uuid4(),
                code="Liabilities:CreditCard",
                name="Credit Card",
                account_type=AccountType.LIABILITY,
                currency="USD",
                is_active=False,  # Inactive account
            ),
        ]

    def test_list_all_accounts(self, use_case, mock_uow, sample_accounts):
        """Test listing all active accounts."""
        # Arrange
        mock_uow.accounts.list_all.return_value = sample_accounts

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 5  # Only active accounts by default
        assert all(acc.code for acc in result)
        mock_uow.accounts.list_all.assert_called_once()

    def test_list_accounts_with_inactive(self, use_case, mock_uow, sample_accounts):
        """Test listing all accounts including inactive."""
        # Arrange
        mock_uow.accounts.list_all.return_value = sample_accounts

        # Act
        result = use_case.execute(include_inactive=True)

        # Assert
        assert len(result) == 6  # All accounts including inactive
        assert any(acc.code == "Liabilities:CreditCard" for acc in result)

    def test_list_accounts_filter_by_type_asset(
        self, use_case, mock_uow, sample_accounts
    ):
        """Test filtering accounts by ASSET type."""
        # Arrange
        mock_uow.accounts.list_all.return_value = sample_accounts

        # Act
        result = use_case.execute(account_type=AccountType.ASSET)

        # Assert
        assert len(result) == 2  # Only ASSET accounts
        assert all(acc.type == "ASSET" for acc in result)
        assert any(acc.code == "Assets:Checking" for acc in result)
        assert any(acc.code == "Assets:Savings" for acc in result)

    def test_list_accounts_filter_by_type_expense(
        self, use_case, mock_uow, sample_accounts
    ):
        """Test filtering accounts by EXPENSE type."""
        # Arrange
        mock_uow.accounts.list_all.return_value = sample_accounts

        # Act
        result = use_case.execute(account_type=AccountType.EXPENSE)

        # Assert
        assert len(result) == 2  # Only EXPENSE accounts
        assert all(acc.type == "EXPENSE" for acc in result)
        assert any(acc.code == "Expenses:Food" for acc in result)
        assert any(acc.code == "Expenses:Transport" for acc in result)

    def test_list_accounts_filter_by_type_income(
        self, use_case, mock_uow, sample_accounts
    ):
        """Test filtering accounts by INCOME type."""
        # Arrange
        mock_uow.accounts.list_all.return_value = sample_accounts

        # Act
        result = use_case.execute(account_type=AccountType.INCOME)

        # Assert
        assert len(result) == 1  # Only INCOME accounts
        assert result[0].type == "INCOME"
        assert result[0].code == "Income:Salary"

    def test_list_empty_accounts(self, use_case, mock_uow):
        """Test listing when no accounts exist."""
        # Arrange
        mock_uow.accounts.list_all.return_value = []

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 0
        assert result == []

    def test_list_accounts_dto_structure(self, use_case, mock_uow, sample_accounts):
        """Test that returned DTOs have correct structure."""
        # Arrange
        mock_uow.accounts.list_all.return_value = sample_accounts[:1]

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 1
        account_dto = result[0]
        assert hasattr(account_dto, "id")
        assert hasattr(account_dto, "code")
        assert hasattr(account_dto, "name")
        assert hasattr(account_dto, "type")
        assert hasattr(account_dto, "currency")
        assert hasattr(account_dto, "balance")
        assert account_dto.currency == "USD"

    def test_list_accounts_filter_type_with_inactive(
        self, use_case, mock_uow, sample_accounts
    ):
        """Test filtering by type and including inactive accounts."""
        # Arrange
        mock_uow.accounts.list_all.return_value = sample_accounts

        # Act
        result = use_case.execute(
            account_type=AccountType.LIABILITY, include_inactive=True
        )

        # Assert
        assert len(result) == 1
        assert result[0].type == "LIABILITY"
        assert result[0].code == "Liabilities:CreditCard"
