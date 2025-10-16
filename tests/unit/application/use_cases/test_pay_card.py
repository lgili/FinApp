"""Unit tests for PayCardUseCase."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
import pytest

from finlite.application.use_cases.pay_card import (
    PayCardCommand,
    PayCardUseCase,
)
from finlite.domain.entities.account import Account
from finlite.domain.value_objects.account_type import AccountType


class TestPayCardUseCase:
    """Test suite for PayCardUseCase."""

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
        return PayCardUseCase(
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
        checking = Account.create(
            code="Assets:Checking",
            name="Checking Account",
            account_type=AccountType.ASSET,
            currency="BRL",
        )
        return {"card": card, "checking": checking}

    def test_pay_card_success(
        self, use_case, mock_uow, mock_account_repo, mock_transaction_repo, sample_accounts
    ):
        """Test successful card payment."""
        # Arrange
        card = sample_accounts["card"]
        checking = sample_accounts["checking"]

        command = PayCardCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            payment_account_code="Assets:Checking",
            amount=Decimal("1500.00"),
            currency="BRL",
            date=datetime(2025, 10, 5),
            description="October invoice payment",
        )

        # Mock repository behavior
        def find_by_code(code):
            if code == "Liabilities:CreditCard:Nubank":
                return card
            elif code == "Assets:Checking":
                return checking
            return None

        mock_account_repo.find_by_code.side_effect = find_by_code

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.card_account_code == "Liabilities:CreditCard:Nubank"
        assert result.payment_account_code == "Assets:Checking"
        assert result.amount == Decimal("1500.00")
        assert result.currency == "BRL"
        assert result.date == datetime(2025, 10, 5)
        assert result.transaction_id is not None

        # Verify transaction was added
        mock_transaction_repo.add.assert_called_once()

        # Verify commit was called
        mock_uow.commit.assert_called_once()

        # Verify the transaction has correct postings
        added_transaction = mock_transaction_repo.add.call_args[0][0]
        assert len(added_transaction.postings) == 2

        # Card posting (debit - reduces debt)
        card_posting = [p for p in added_transaction.postings if p.account_id == card.id][0]
        assert card_posting.amount.amount == Decimal("1500.00")
        assert card_posting.is_debit()

        # Checking posting (credit - money out)
        checking_posting = [
            p for p in added_transaction.postings if p.account_id == checking.id
        ][0]
        assert checking_posting.amount.amount == Decimal("-1500.00")
        assert checking_posting.is_credit()

        # Verify transaction has tag
        assert "card-payment" in added_transaction.tags

    def test_pay_card_account_not_found(self, use_case, mock_uow, mock_account_repo):
        """Test error when card account doesn't exist."""
        # Arrange
        command = PayCardCommand(
            card_account_code="Liabilities:CreditCard:NonExistent",
            payment_account_code="Assets:Checking",
            amount=Decimal("1000.00"),
            currency="BRL",
            date=datetime(2025, 10, 5),
        )

        mock_account_repo.find_by_code.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(command)

        assert "Card account not found" in str(exc_info.value)
        assert "NonExistent" in str(exc_info.value)

    def test_pay_card_not_liability_account(
        self, use_case, mock_uow, mock_account_repo
    ):
        """Test error when card account is not LIABILITY type."""
        # Arrange
        asset_account = Account.create(
            code="Assets:Savings",
            name="Savings Account",
            account_type=AccountType.ASSET,  # Not LIABILITY!
            currency="BRL",
        )

        command = PayCardCommand(
            card_account_code="Assets:Savings",
            payment_account_code="Assets:Checking",
            amount=Decimal("1000.00"),
            currency="BRL",
            date=datetime(2025, 10, 5),
        )

        mock_account_repo.find_by_code.return_value = asset_account

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(command)

        assert "not a LIABILITY account" in str(exc_info.value)

    def test_pay_card_payment_account_not_found(
        self, use_case, mock_uow, mock_account_repo, sample_accounts
    ):
        """Test error when payment account doesn't exist."""
        # Arrange
        card = sample_accounts["card"]

        command = PayCardCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            payment_account_code="Assets:NonExistent",
            amount=Decimal("1000.00"),
            currency="BRL",
            date=datetime(2025, 10, 5),
        )

        def find_by_code(code):
            if code == "Liabilities:CreditCard:Nubank":
                return card
            return None

        mock_account_repo.find_by_code.side_effect = find_by_code

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(command)

        assert "Payment account not found" in str(exc_info.value)
        assert "NonExistent" in str(exc_info.value)

    def test_pay_card_payment_account_not_asset(
        self, use_case, mock_uow, mock_account_repo, sample_accounts
    ):
        """Test error when payment account is not ASSET type."""
        # Arrange
        card = sample_accounts["card"]
        expense_account = Account.create(
            code="Expenses:Food",
            name="Food Expenses",
            account_type=AccountType.EXPENSE,  # Not ASSET!
            currency="BRL",
        )

        command = PayCardCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            payment_account_code="Expenses:Food",
            amount=Decimal("1000.00"),
            currency="BRL",
            date=datetime(2025, 10, 5),
        )

        def find_by_code(code):
            if code == "Liabilities:CreditCard:Nubank":
                return card
            elif code == "Expenses:Food":
                return expense_account
            return None

        mock_account_repo.find_by_code.side_effect = find_by_code

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(command)

        assert "not an ASSET account" in str(exc_info.value)

    def test_pay_card_negative_amount(
        self, use_case, mock_uow, mock_account_repo, sample_accounts
    ):
        """Test error when payment amount is negative."""
        # Arrange
        command = PayCardCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            payment_account_code="Assets:Checking",
            amount=Decimal("-500.00"),  # Negative!
            currency="BRL",
            date=datetime(2025, 10, 5),
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(command)

        assert "must be positive" in str(exc_info.value)

    def test_pay_card_zero_amount(
        self, use_case, mock_uow, mock_account_repo, sample_accounts
    ):
        """Test error when payment amount is zero."""
        # Arrange
        command = PayCardCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            payment_account_code="Assets:Checking",
            amount=Decimal("0.00"),  # Zero!
            currency="BRL",
            date=datetime(2025, 10, 5),
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(command)

        assert "must be positive" in str(exc_info.value)

    def test_pay_card_custom_description(
        self, use_case, mock_uow, mock_account_repo, mock_transaction_repo, sample_accounts
    ):
        """Test payment with custom description."""
        # Arrange
        card = sample_accounts["card"]
        checking = sample_accounts["checking"]

        command = PayCardCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            payment_account_code="Assets:Checking",
            amount=Decimal("2500.00"),
            currency="BRL",
            date=datetime(2025, 10, 15),
            description="Full payment - October statement",
        )

        def find_by_code(code):
            if code == "Liabilities:CreditCard:Nubank":
                return card
            elif code == "Assets:Checking":
                return checking
            return None

        mock_account_repo.find_by_code.side_effect = find_by_code

        # Act
        result = use_case.execute(command)

        # Assert
        added_transaction = mock_transaction_repo.add.call_args[0][0]
        assert added_transaction.description == "Full payment - October statement"

    def test_pay_card_transaction_is_balanced(
        self, use_case, mock_uow, mock_account_repo, mock_transaction_repo, sample_accounts
    ):
        """Test that generated transaction is balanced."""
        # Arrange
        card = sample_accounts["card"]
        checking = sample_accounts["checking"]

        command = PayCardCommand(
            card_account_code="Liabilities:CreditCard:Nubank",
            payment_account_code="Assets:Checking",
            amount=Decimal("750.50"),
            currency="BRL",
            date=datetime(2025, 10, 20),
        )

        def find_by_code(code):
            if code == "Liabilities:CreditCard:Nubank":
                return card
            elif code == "Assets:Checking":
                return checking
            return None

        mock_account_repo.find_by_code.side_effect = find_by_code

        # Act
        result = use_case.execute(command)

        # Assert
        added_transaction = mock_transaction_repo.add.call_args[0][0]
        assert added_transaction.is_balanced()

        # Verify sum of postings is zero
        total = sum(p.amount.amount for p in added_transaction.postings)
        assert total == Decimal("0")
