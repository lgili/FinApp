"""Unit tests for RecordTransactionUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
import pytest

from finlite.application.dtos import CreateTransactionDTO, CreatePostingDTO
from finlite.application.use_cases import RecordTransactionUseCase
from finlite.domain.entities import Account, Transaction
from finlite.domain.exceptions import AccountNotFoundError, UnbalancedTransactionError
from finlite.domain.value_objects import AccountType, Posting, Money


class TestRecordTransactionUseCase:
    """Test suite for RecordTransactionUseCase."""

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
        return RecordTransactionUseCase(uow=mock_uow)

    @pytest.fixture
    def sample_accounts(self):
        """Create sample accounts for testing."""
        checking = Account(
            id=uuid4(),
            name="Assets:Checking",
            account_type=AccountType.ASSET,
            currency="USD",
        )
        food = Account(
            id=uuid4(),
            name="Expenses:Food",
            account_type=AccountType.EXPENSE,
            currency="USD",
        )
        return {"checking": checking, "food": food}

    def test_record_transaction_success(self, use_case, mock_uow, sample_accounts):
        """Test successful transaction recording."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]

        dto = CreateTransactionDTO(
            date=date(2025, 10, 1),
            description="Grocery shopping",
            postings=(
                CreatePostingDTO(
                    account_code="Assets:Checking",
                    amount=Decimal("-50.00"),
                    currency="USD",
                ),
                CreatePostingDTO(
                    account_code="Expenses:Food",
                    amount=Decimal("50.00"),
                    currency="USD",
                ),
            ),
        )

        # Mock repository behavior
        def find_by_code(code):
            if code == "Assets:Checking":
                return checking
            elif code == "Expenses:Food":
                return food
            return None

        mock_uow.accounts.find_by_code.side_effect = find_by_code

        # Create expected transaction
        expected_transaction = Transaction(
            id=uuid4(),
            date=date(2025, 10, 1),
            description="Grocery shopping",
            postings=(
                Posting(
                    account_id=checking.id,
                    amount=Money(Decimal("-50.00"), "USD"),
                ),
                Posting(
                    account_id=food.id,
                    amount=Money(Decimal("50.00"), "USD"),
                ),
            ),
        )
        mock_uow.transactions.add.return_value = expected_transaction

        # Act
        result = use_case.execute(dto)

        # Assert
        assert result.recorded is True
        assert result.transaction.description == "Grocery shopping"
        assert len(result.transaction.postings) == 2
        assert result.transaction.postings[0].account_code == "Assets:Checking"
        assert result.transaction.postings[0].amount == Decimal("-50.00")
        assert result.transaction.postings[1].account_code == "Expenses:Food"
        assert result.transaction.postings[1].amount == Decimal("50.00")

        mock_uow.transactions.add.assert_called_once()
        mock_uow.commit.assert_called_once()

    def test_record_transaction_account_not_found(self, use_case, mock_uow):
        """Test recording transaction with non-existent account."""
        # Arrange
        dto = CreateTransactionDTO(
            date=date(2025, 10, 1),
            description="Test transaction",
            postings=(
                CreatePostingDTO(
                    account_code="NonExistent:Account",
                    amount=Decimal("-100.00"),
                    currency="USD",
                ),
                CreatePostingDTO(
                    account_code="Expenses:Food",
                    amount=Decimal("100.00"),
                    currency="USD",
                ),
            ),
        )

        # Mock - first account doesn't exist
        mock_uow.accounts.find_by_code.return_value = None

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc_info:
            use_case.execute(dto)

        assert "NonExistent:Account" in str(exc_info.value)
        mock_uow.transactions.add.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_record_transaction_with_tags(self, use_case, mock_uow, sample_accounts):
        """Test recording transaction with tags."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]

        dto = CreateTransactionDTO(
            date=date(2025, 10, 1),
            description="Restaurant",
            postings=(
                CreatePostingDTO(
                    account_code="Assets:Checking",
                    amount=Decimal("-75.00"),
                    currency="USD",
                ),
                CreatePostingDTO(
                    account_code="Expenses:Food",
                    amount=Decimal("75.00"),
                    currency="USD",
                ),
            ),
            tags=("restaurant", "dinner"),
        )

        def find_by_code(code):
            return checking if code == "Assets:Checking" else food

        mock_uow.accounts.find_by_code.side_effect = find_by_code

        expected_transaction = Transaction(
            id=uuid4(),
            date=date(2025, 10, 1),
            description="Restaurant",
            postings=(
                Posting(checking.id, Money(Decimal("-75.00"), "USD")),
                Posting(food.id, Money(Decimal("75.00"), "USD")),
            ),
            tags=("restaurant", "dinner"),
        )
        mock_uow.transactions.add.return_value = expected_transaction

        # Act
        result = use_case.execute(dto)

        # Assert
        assert result.recorded is True
        assert result.transaction.tags == ("restaurant", "dinner")

    def test_record_transaction_with_note(self, use_case, mock_uow, sample_accounts):
        """Test recording transaction with note."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]

        dto = CreateTransactionDTO(
            date=date(2025, 10, 1),
            description="Supermarket",
            postings=(
                CreatePostingDTO(
                    account_code="Assets:Checking",
                    amount=Decimal("-120.50"),
                    currency="USD",
                ),
                CreatePostingDTO(
                    account_code="Expenses:Food",
                    amount=Decimal("120.50"),
                    currency="USD",
                ),
            ),
            note="Weekly groceries - Whole Foods",
        )

        def find_by_code(code):
            return checking if code == "Assets:Checking" else food

        mock_uow.accounts.find_by_code.side_effect = find_by_code

        expected_transaction = Transaction(
            id=uuid4(),
            date=date(2025, 10, 1),
            description="Supermarket",
            postings=(
                Posting(checking.id, Money(Decimal("-120.50"), "USD")),
                Posting(food.id, Money(Decimal("120.50"), "USD")),
            ),
            notes="Weekly groceries - Whole Foods",
        )
        mock_uow.transactions.add.return_value = expected_transaction

        # Act
        result = use_case.execute(dto)

        # Assert
        assert result.recorded is True
        assert result.transaction.note == "Weekly groceries - Whole Foods"

    def test_record_transaction_multiple_postings(
        self, use_case, mock_uow, sample_accounts
    ):
        """Test recording transaction with more than 2 postings."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        transport = Account(
            id=uuid4(),
            name="Expenses:Transport",
            account_type=AccountType.EXPENSE,
            currency="USD",
        )

        dto = CreateTransactionDTO(
            date=date(2025, 10, 1),
            description="Split payment",
            postings=(
                CreatePostingDTO(
                    account_code="Assets:Checking",
                    amount=Decimal("-150.00"),
                    currency="USD",
                ),
                CreatePostingDTO(
                    account_code="Expenses:Food",
                    amount=Decimal("100.00"),
                    currency="USD",
                ),
                CreatePostingDTO(
                    account_code="Expenses:Transport",
                    amount=Decimal("50.00"),
                    currency="USD",
                ),
            ),
        )

        def find_by_code(code):
            if code == "Assets:Checking":
                return checking
            elif code == "Expenses:Food":
                return food
            elif code == "Expenses:Transport":
                return transport
            return None

        mock_uow.accounts.find_by_code.side_effect = find_by_code

        expected_transaction = Transaction(
            id=uuid4(),
            date=date(2025, 10, 1),
            description="Split payment",
            postings=(
                Posting(checking.id, Money(Decimal("-150.00"), "USD")),
                Posting(food.id, Money(Decimal("100.00"), "USD")),
                Posting(transport.id, Money(Decimal("50.00"), "USD")),
            ),
        )
        mock_uow.transactions.add.return_value = expected_transaction

        # Act
        result = use_case.execute(dto)

        # Assert
        assert result.recorded is True
        assert len(result.transaction.postings) == 3
        assert result.transaction.postings[0].amount == Decimal("-150.00")
        assert result.transaction.postings[1].amount == Decimal("100.00")
        assert result.transaction.postings[2].amount == Decimal("50.00")
