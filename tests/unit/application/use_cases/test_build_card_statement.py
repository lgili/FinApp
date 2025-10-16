"""Unit tests for BuildCardStatementUseCase."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
import pytest

from finlite.application.use_cases.build_card_statement import (
    BuildCardStatementCommand,
    BuildCardStatementUseCase,
)
from finlite.domain.entities.account import Account
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting


class TestBuildCardStatementUseCase:
    """Test suite for BuildCardStatementUseCase."""

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = Mock()
        uow.__enter__ = Mock(return_value=uow)
        uow.__exit__ = Mock(return_value=False)
        return uow

    @pytest.fixture
    def mock_account_repo(self):
        """Create mock account repository."""
        return Mock()

    @pytest.fixture
    def mock_transaction_repo(self):
        """Create mock transaction repository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_uow, mock_account_repo, mock_transaction_repo):
        """Create use case instance."""
        return BuildCardStatementUseCase(
            uow=mock_uow,
            account_repository=mock_account_repo,
            transaction_repository=mock_transaction_repo,
        )

    @pytest.fixture
    def sample_accounts(self):
        """Create sample accounts for testing."""
        card = Account.create(
            code="Liabilities:CreditCard:Nubank",
            name="Nubank Credit Card",
            account_type=AccountType.LIABILITY,
            currency="BRL",
        )
        food = Account.create(
            code="Expenses:Food",
            name="Food Expenses",
            account_type=AccountType.EXPENSE,
            currency="BRL",
        )
        transport = Account.create(
            code="Expenses:Transport",
            name="Transport Expenses",
            account_type=AccountType.EXPENSE,
            currency="BRL",
        )
        return {"card": card, "food": food, "transport": transport}

    def test_build_statement_success(
        self, use_case, mock_uow, mock_account_repo, mock_transaction_repo, sample_accounts
    ):
        """Test successful card statement generation."""
        # Arrange
        card = sample_accounts["card"]
        food = sample_accounts["food"]
        transport = sample_accounts["transport"]

        # Create sample transactions
        tx1 = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Restaurant lunch",
            postings=[
                Posting(card.id, Money.from_float(-50.0, "BRL")),  # Credit = charge
                Posting(food.id, Money.from_float(50.0, "BRL")),
            ],
        )

        tx2 = Transaction.create(
            date=datetime(2025, 10, 10).date(),
            description="Uber ride",
            postings=[
                Posting(card.id, Money.from_float(-30.0, "BRL")),  # Credit = charge
                Posting(transport.id, Money.from_float(30.0, "BRL")),
            ],
        )

        command = BuildCardStatementCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            from_date=datetime(2025, 10, 1),
            to_date=datetime(2025, 10, 31),
            currency="BRL",
        )

        # Mock repository behavior
        mock_account_repo.find_by_code.return_value = card
        mock_account_repo.list_all.return_value = [card, food, transport]
        mock_transaction_repo.find_by_date_range.return_value = [tx1, tx2]

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.card_account_code == "Liabilities:CreditCard:Nubank"
        assert result.card_account_name == "Nubank Credit Card"
        assert result.currency == "BRL"
        assert result.item_count == 2
        assert result.total_amount == Decimal("80.0")  # 50 + 30
        assert len(result.items) == 2

        # Check first item
        assert result.items[0].description == "Restaurant lunch"
        assert result.items[0].amount == Decimal("50.0")
        assert result.items[0].category_code == "Expenses:Food"

        # Check second item
        assert result.items[1].description == "Uber ride"
        assert result.items[1].amount == Decimal("30.0")
        assert result.items[1].category_code == "Expenses:Transport"

    def test_build_statement_account_not_found(
        self, use_case, mock_uow, mock_account_repo
    ):
        """Test error when card account doesn't exist."""
        # Arrange
        command = BuildCardStatementCommand(
            card_account_code="Liabilities:CreditCard:NonExistent",
            from_date=datetime(2025, 10, 1),
            to_date=datetime(2025, 10, 31),
            currency="BRL",
        )

        mock_account_repo.find_by_code.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(command)

        assert "Card account not found" in str(exc_info.value)
        assert "NonExistent" in str(exc_info.value)

    def test_build_statement_not_liability_account(
        self, use_case, mock_uow, mock_account_repo
    ):
        """Test error when account is not LIABILITY type."""
        # Arrange
        asset_account = Account.create(
            code="Assets:Checking",
            name="Checking Account",
            account_type=AccountType.ASSET,  # Not LIABILITY!
            currency="BRL",
        )

        command = BuildCardStatementCommand(
            card_account_code="Assets:Checking",
            from_date=datetime(2025, 10, 1),
            to_date=datetime(2025, 10, 31),
            currency="BRL",
        )

        mock_account_repo.find_by_code.return_value = asset_account

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(command)

        assert "not a LIABILITY account" in str(exc_info.value)

    def test_build_statement_empty_period(
        self, use_case, mock_uow, mock_account_repo, mock_transaction_repo, sample_accounts
    ):
        """Test statement generation with no transactions."""
        # Arrange
        card = sample_accounts["card"]

        command = BuildCardStatementCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            from_date=datetime(2025, 10, 1),
            to_date=datetime(2025, 10, 31),
            currency="BRL",
        )

        mock_account_repo.find_by_code.return_value = card
        mock_account_repo.list_all.return_value = [card]
        mock_transaction_repo.find_by_date_range.return_value = []  # No transactions

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.item_count == 0
        assert result.total_amount == Decimal("0")
        assert len(result.items) == 0

    def test_build_statement_ignores_payments(
        self, use_case, mock_uow, mock_account_repo, mock_transaction_repo, sample_accounts
    ):
        """Test that statement only includes charges, not payments."""
        # Arrange
        card = sample_accounts["card"]
        food = sample_accounts["food"]
        checking = Account.create(
            code="Assets:Checking",
            name="Checking Account",
            account_type=AccountType.ASSET,
            currency="BRL",
        )

        # Charge transaction
        tx_charge = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Restaurant",
            postings=[
                Posting(card.id, Money.from_float(-100.0, "BRL")),  # Credit = charge
                Posting(food.id, Money.from_float(100.0, "BRL")),
            ],
        )

        # Payment transaction (should be ignored)
        tx_payment = Transaction.create(
            date=datetime(2025, 10, 15).date(),
            description="Card payment",
            postings=[
                Posting(card.id, Money.from_float(100.0, "BRL")),  # Debit = payment
                Posting(checking.id, Money.from_float(-100.0, "BRL")),
            ],
        )

        command = BuildCardStatementCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            from_date=datetime(2025, 10, 1),
            to_date=datetime(2025, 10, 31),
            currency="BRL",
        )

        mock_account_repo.find_by_code.return_value = card
        mock_account_repo.list_all.return_value = [card, food, checking]
        mock_transaction_repo.find_by_date_range.return_value = [tx_charge, tx_payment]

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.item_count == 1  # Only the charge, not the payment
        assert result.total_amount == Decimal("100.0")
        assert result.items[0].description == "Restaurant"

    def test_build_statement_items_sorted_by_date(
        self, use_case, mock_uow, mock_account_repo, mock_transaction_repo, sample_accounts
    ):
        """Test that statement items are sorted chronologically."""
        # Arrange
        card = sample_accounts["card"]
        food = sample_accounts["food"]

        # Create transactions in random order
        tx1 = Transaction.create(
            date=datetime(2025, 10, 15).date(),
            description="Mid month",
            postings=[
                Posting(card.id, Money.from_float(-50.0, "BRL")),
                Posting(food.id, Money.from_float(50.0, "BRL")),
            ],
        )

        tx2 = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Early month",
            postings=[
                Posting(card.id, Money.from_float(-30.0, "BRL")),
                Posting(food.id, Money.from_float(30.0, "BRL")),
            ],
        )

        tx3 = Transaction.create(
            date=datetime(2025, 10, 25).date(),
            description="Late month",
            postings=[
                Posting(card.id, Money.from_float(-20.0, "BRL")),
                Posting(food.id, Money.from_float(20.0, "BRL")),
            ],
        )

        command = BuildCardStatementCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            from_date=datetime(2025, 10, 1),
            to_date=datetime(2025, 10, 31),
            currency="BRL",
        )

        mock_account_repo.find_by_code.return_value = card
        mock_account_repo.list_all.return_value = [card, food]
        mock_transaction_repo.find_by_date_range.return_value = [tx1, tx2, tx3]

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.item_count == 3
        # Check items are sorted by date
        assert result.items[0].description == "Early month"
        assert result.items[1].description == "Mid month"
        assert result.items[2].description == "Late month"
