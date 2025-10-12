"""Unit tests for CreateAccountUseCase."""

from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
import pytest

from finlite.application.dtos import CreateAccountDTO
from finlite.application.use_cases import CreateAccountUseCase
from finlite.domain.entities import Account
from finlite.domain.exceptions import AccountAlreadyExistsError
from finlite.domain.value_objects import AccountType


class TestCreateAccountUseCase:
    """Test suite for CreateAccountUseCase."""

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
        return CreateAccountUseCase(uow=mock_uow)

    def test_create_account_success(self, use_case, mock_uow):
        """Test successful account creation."""
        # Arrange
        dto = CreateAccountDTO(
            code="Assets:Bank:Checking",
            name="Checking Account",
            type="ASSET",
            currency="USD",
        )

        # Mock repository behavior
        mock_uow.accounts.find_by_code.return_value = None  # Account doesn't exist

        created_account = Account(
            id=uuid4(),
            name="Assets:Bank:Checking",
            account_type=AccountType.ASSET,
            currency="USD",
        )
        mock_uow.accounts.add.return_value = created_account

        # Act
        result = use_case.execute(dto)

        # Assert
        assert result.created is True
        assert result.account.code == "Assets:Bank:Checking"
        assert result.account.name == "Assets:Bank:Checking"
        assert result.account.type == "ASSET"
        assert result.account.currency == "USD"

        mock_uow.accounts.find_by_code.assert_called_once_with("Assets:Bank:Checking")
        mock_uow.accounts.add.assert_called_once()
        mock_uow.commit.assert_called_once()

    def test_create_account_already_exists(self, use_case, mock_uow):
        """Test creating account that already exists raises error."""
        # Arrange
        dto = CreateAccountDTO(
            code="Assets:Bank:Checking",
            name="Checking Account",
            type="ASSET",
            currency="USD",
        )

        # Mock existing account
        existing_account = Account(
            id=uuid4(),
            name="Assets:Bank:Checking",
            account_type=AccountType.ASSET,
            currency="USD",
        )
        mock_uow.accounts.find_by_code.return_value = existing_account

        # Act & Assert
        with pytest.raises(AccountAlreadyExistsError) as exc_info:
            use_case.execute(dto)

        assert "Assets:Bank:Checking" in str(exc_info.value)
        mock_uow.accounts.add.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_create_account_different_types(self, use_case, mock_uow):
        """Test creating accounts of different types."""
        for account_type in ["ASSET", "LIABILITY", "EQUITY", "INCOME", "EXPENSE"]:
            dto = CreateAccountDTO(
                code=f"Test:{account_type}",
                name=f"{account_type} Account",
                type=account_type,
                currency="BRL",
            )

            mock_uow.accounts.find_by_code.return_value = None
            created_account = Account(
                id=uuid4(),
                name=f"Test:{account_type}",
                account_type=AccountType[account_type],
                currency="BRL",
            )
            mock_uow.accounts.add.return_value = created_account

            # Act
            result = use_case.execute(dto)

            # Assert
            assert result.created is True
            assert result.account.type == account_type
