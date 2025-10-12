"""Unit tests for ListTransactionsUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
import pytest

from finlite.application.dtos import TransactionFilterDTO
from finlite.application.use_cases import ListTransactionsUseCase
from finlite.domain.entities import Account, Transaction
from finlite.domain.value_objects import AccountType, Posting, Money


class TestListTransactionsUseCase:
    """Test suite for ListTransactionsUseCase."""

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
        return ListTransactionsUseCase(uow=mock_uow)

    @pytest.fixture
    def sample_accounts(self):
        """Create sample accounts."""
        return {
            "checking": Account(
                id=uuid4(),
                name="Assets:Checking",
                account_type=AccountType.ASSET,
                currency="USD",
            ),
            "food": Account(
                id=uuid4(),
                name="Expenses:Food",
                account_type=AccountType.EXPENSE,
                currency="USD",
            ),
        }

    @pytest.fixture
    def sample_transactions(self, sample_accounts):
        """Create sample transactions."""
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]

        return [
            Transaction(
                id=uuid4(),
                date=date(2025, 10, 1),
                description="Grocery shopping",
                postings=(
                    Posting(checking.id, Money(Decimal("-50.00"), "USD")),
                    Posting(food.id, Money(Decimal("50.00"), "USD")),
                ),
            ),
            Transaction(
                id=uuid4(),
                date=date(2025, 10, 2),
                description="Restaurant",
                postings=(
                    Posting(checking.id, Money(Decimal("-75.00"), "USD")),
                    Posting(food.id, Money(Decimal("75.00"), "USD")),
                ),
                tags=("restaurant", "dinner"),
            ),
            Transaction(
                id=uuid4(),
                date=date(2025, 10, 3),
                description="Supermarket",
                postings=(
                    Posting(checking.id, Money(Decimal("-120.50"), "USD")),
                    Posting(food.id, Money(Decimal("120.50"), "USD")),
                ),
                notes="Weekly groceries",
            ),
        ]

    def test_list_all_transactions_no_filter(
        self, use_case, mock_uow, sample_transactions, sample_accounts
    ):
        """Test listing all transactions without filters."""
        # Arrange
        mock_uow.transactions.list_all.return_value = sample_transactions
        
        # Mock account lookups for DTO conversion
        def get_account(account_id):
            for acc in sample_accounts.values():
                if acc.id == account_id:
                    return acc
            raise ValueError(f"Account {account_id} not found")
        
        mock_uow.accounts.get.side_effect = get_account

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 3
        assert all(txn.description for txn in result)
        mock_uow.transactions.list_all.assert_called_once_with(limit=100)

    def test_list_transactions_with_date_range(
        self, use_case, mock_uow, sample_transactions, sample_accounts
    ):
        """Test listing transactions with date range filter."""
        # Arrange
        filter_dto = TransactionFilterDTO(
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 2),
        )
        mock_uow.transactions.find_by_date_range.return_value = sample_transactions[:2]
        
        def get_account(account_id):
            for acc in sample_accounts.values():
                if acc.id == account_id:
                    return acc
            raise ValueError(f"Account {account_id} not found")
        
        mock_uow.accounts.get.side_effect = get_account

        # Act
        result = use_case.execute(filter_dto)

        # Assert
        assert len(result) == 2
        mock_uow.transactions.find_by_date_range.assert_called_once_with(
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 2),
            account_id=None,
        )

    def test_list_transactions_by_account(
        self, use_case, mock_uow, sample_transactions, sample_accounts
    ):
        """Test listing transactions filtered by account."""
        # Arrange
        checking = sample_accounts["checking"]
        filter_dto = TransactionFilterDTO(
            account_code="Assets:Checking",
            limit=50,
        )
        mock_uow.accounts.find_by_code.return_value = checking
        mock_uow.transactions.find_by_account.return_value = sample_transactions
        
        def get_account(account_id):
            for acc in sample_accounts.values():
                if acc.id == account_id:
                    return acc
            raise ValueError(f"Account {account_id} not found")
        
        mock_uow.accounts.get.side_effect = get_account

        # Act
        result = use_case.execute(filter_dto)

        # Assert
        assert len(result) == 3
        mock_uow.accounts.find_by_code.assert_called_with("Assets:Checking")
        mock_uow.transactions.find_by_account.assert_called_once_with(
            account_id=checking.id,
            limit=50,
        )

    def test_list_transactions_by_description(
        self, use_case, mock_uow, sample_transactions, sample_accounts
    ):
        """Test listing transactions by description search."""
        # Arrange
        filter_dto = TransactionFilterDTO(
            description="super",
            limit=10,
        )
        mock_uow.transactions.search_description.return_value = [
            sample_transactions[2]
        ]
        
        def get_account(account_id):
            for acc in sample_accounts.values():
                if acc.id == account_id:
                    return acc
            raise ValueError(f"Account {account_id} not found")
        
        mock_uow.accounts.get.side_effect = get_account

        # Act
        result = use_case.execute(filter_dto)

        # Assert
        assert len(result) == 1
        assert result[0].description == "Supermarket"
        mock_uow.transactions.search_description.assert_called_once_with(
            pattern="super",
            limit=10,
        )

    def test_list_transactions_by_tags(
        self, use_case, mock_uow, sample_transactions, sample_accounts
    ):
        """Test listing transactions by tags."""
        # Arrange
        filter_dto = TransactionFilterDTO(
            tags=("restaurant", "dinner"),
        )
        mock_uow.transactions.find_by_tags.return_value = [sample_transactions[1]]
        
        def get_account(account_id):
            for acc in sample_accounts.values():
                if acc.id == account_id:
                    return acc
            raise ValueError(f"Account {account_id} not found")
        
        mock_uow.accounts.get.side_effect = get_account

        # Act
        result = use_case.execute(filter_dto)

        # Assert
        assert len(result) == 1
        assert result[0].tags == ("restaurant", "dinner")
        mock_uow.transactions.find_by_tags.assert_called_once_with(
            tags=["restaurant", "dinner"],
            match_all=True,
        )

    def test_list_empty_transactions(self, use_case, mock_uow):
        """Test listing when no transactions exist."""
        # Arrange
        mock_uow.transactions.list_all.return_value = []

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 0
        assert result == []

    def test_list_transactions_dto_structure(
        self, use_case, mock_uow, sample_transactions, sample_accounts
    ):
        """Test that returned DTOs have correct structure."""
        # Arrange
        mock_uow.transactions.list_all.return_value = sample_transactions[:1]
        
        def get_account(account_id):
            for acc in sample_accounts.values():
                if acc.id == account_id:
                    return acc
            raise ValueError(f"Account {account_id} not found")
        
        mock_uow.accounts.get.side_effect = get_account

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 1
        txn_dto = result[0]
        assert hasattr(txn_dto, "id")
        assert hasattr(txn_dto, "date")
        assert hasattr(txn_dto, "description")
        assert hasattr(txn_dto, "postings")
        assert hasattr(txn_dto, "tags")
        assert hasattr(txn_dto, "payee")
        assert hasattr(txn_dto, "note")
        assert len(txn_dto.postings) == 2
        
        # Check posting structure
        posting = txn_dto.postings[0]
        assert hasattr(posting, "account_code")
        assert hasattr(posting, "amount")
        assert hasattr(posting, "currency")

    def test_list_transactions_with_custom_limit(
        self, use_case, mock_uow, sample_transactions, sample_accounts
    ):
        """Test listing transactions with custom limit."""
        # Arrange
        filter_dto = TransactionFilterDTO(limit=5)
        mock_uow.transactions.list_all.return_value = sample_transactions
        
        def get_account(account_id):
            for acc in sample_accounts.values():
                if acc.id == account_id:
                    return acc
            raise ValueError(f"Account {account_id} not found")
        
        mock_uow.accounts.get.side_effect = get_account

        # Act
        result = use_case.execute(filter_dto)

        # Assert
        assert len(result) == 3
        mock_uow.transactions.list_all.assert_called_once_with(
            limit=5,
            order_by="date",
        )
