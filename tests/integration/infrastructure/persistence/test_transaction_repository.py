"""
Integration tests for SqlAlchemyTransactionRepository.

These tests validate:
- Domain Transaction Entity → Mapper → ORM Model → Database
- Database → ORM Model → Mapper → Domain Transaction Entity
- Complex queries (date ranges, accounts, tags, etc.)
- Transaction + Postings persistence (aggregate root)
"""
import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from finlite.domain.entities.account import Account
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting
from finlite.domain.exceptions import TransactionNotFoundError
from finlite.infrastructure.persistence.sqlalchemy.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository
)
from finlite.infrastructure.persistence.sqlalchemy.repositories.account_repository import (
    SqlAlchemyAccountRepository
)
from finlite.infrastructure.persistence.sqlalchemy.models import TransactionModel


class SimpleUnitOfWorkWithTransactions:
    """Simplified UnitOfWork for testing both repositories."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None
        self.accounts = None
        self.transactions = None
    
    def __enter__(self):
        self.session = self.session_factory()
        self.accounts = SqlAlchemyAccountRepository(self.session)
        self.transactions = SqlAlchemyTransactionRepository(self.session)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            pass  # No auto-commit
        else:
            self.session.rollback()
        self.session.close()
    
    def commit(self):
        """Commit the current transaction."""
        self.session.commit()
    
    def rollback(self):
        """Rollback the current transaction."""
        self.session.rollback()


@pytest.fixture(scope="function")
def uow_with_transactions(session_factory):
    """Create a UnitOfWork with both Account and Transaction repositories."""
    return SimpleUnitOfWorkWithTransactions(session_factory)


@pytest.fixture
def sample_accounts(uow_with_transactions):
    """Create sample accounts for testing."""
    checking = Account.create("Checking", AccountType.ASSET, "BRL")
    food = Account.create("Food", AccountType.EXPENSE, "BRL")
    salary = Account.create("Salary", AccountType.INCOME, "BRL")
    
    with uow_with_transactions:
        uow_with_transactions.accounts.add(checking)
        uow_with_transactions.accounts.add(food)
        uow_with_transactions.accounts.add(salary)
        uow_with_transactions.commit()
    
    return {"checking": checking, "food": food, "salary": salary}


class TestSqlAlchemyTransactionRepository:
    """Integration tests for Transaction repository."""
    
    def test_add_transaction_persists_to_database(self, uow_with_transactions, sample_accounts, session):
        """Test that adding a transaction persists it with postings."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        postings = (
            Posting(account_id=checking.id, amount=Money(Decimal("-50.00"), "BRL")),
            Posting(account_id=food.id, amount=Money(Decimal("50.00"), "BRL")),
        )
        
        transaction = Transaction.create(
            date=date(2025, 10, 15),
            description="Lunch at restaurant",
            postings=postings,
        )
        
        # Act
        with uow_with_transactions:
            uow_with_transactions.transactions.add(transaction)
            uow_with_transactions.commit()
        
        # Assert - Query directly from DB
        db_transaction = session.query(TransactionModel).filter_by(reference=str(transaction.id)).first()
        assert db_transaction is not None
        assert db_transaction.description == "Lunch at restaurant"
        assert len(db_transaction.postings) == 2
        assert db_transaction.occurred_at.date() == date(2025, 10, 15)
    
    def test_get_transaction_retrieves_with_postings(self, uow_with_transactions, sample_accounts):
        """Test that getting a transaction includes all postings."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        postings = (
            Posting(account_id=checking.id, amount=Money(Decimal("-30.00"), "BRL")),
            Posting(account_id=food.id, amount=Money(Decimal("30.00"), "BRL")),
        )
        
        transaction = Transaction.create(
            date=date(2025, 10, 10),
            description="Groceries",
            postings=postings,
        )
        
        with uow_with_transactions:
            uow_with_transactions.transactions.add(transaction)
            uow_with_transactions.commit()
        
        # Act
        with uow_with_transactions:
            retrieved = uow_with_transactions.transactions.get(transaction.id)
        
        # Assert
        assert retrieved.id == transaction.id
        assert retrieved.description == "Groceries"
        assert len(retrieved.postings) == 2
        assert retrieved.is_balanced()
    
    def test_get_nonexistent_transaction_raises_error(self, uow_with_transactions):
        """Test that getting a non-existent transaction raises error."""
        nonexistent_id = uuid4()
        
        with pytest.raises(TransactionNotFoundError):
            with uow_with_transactions:
                uow_with_transactions.transactions.get(nonexistent_id)
    
    def test_find_by_date_range(self, uow_with_transactions, sample_accounts):
        """Test finding transactions by date range."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        # Create 3 transactions in different dates
        transactions = []
        for day in [5, 15, 25]:
            postings = (
                Posting(account_id=checking.id, amount=Money(Decimal("-10.00"), "BRL")),
                Posting(account_id=food.id, amount=Money(Decimal("10.00"), "BRL")),
            )
            tx = Transaction.create(
                date=date(2025, 10, day),
                description=f"Transaction on day {day}",
                postings=postings,
            )
            transactions.append(tx)
        
        with uow_with_transactions:
            for tx in transactions:
                uow_with_transactions.transactions.add(tx)
            uow_with_transactions.commit()
        
        # Act - Find transactions between 10-20
        with uow_with_transactions:
            found = uow_with_transactions.transactions.find_by_date_range(
                start_date=date(2025, 10, 10),
                end_date=date(2025, 10, 20),
            )
        
        # Assert
        assert len(found) == 1
        assert found[0].date == date(2025, 10, 15)
    
    def test_find_by_account(self, uow_with_transactions, sample_accounts):
        """Test finding transactions by account."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        salary = sample_accounts["salary"]
        
        # Transaction 1: Checking -> Food
        postings1 = (
            Posting(account_id=checking.id, amount=Money(Decimal("-20.00"), "BRL")),
            Posting(account_id=food.id, amount=Money(Decimal("20.00"), "BRL")),
        )
        tx1 = Transaction.create(date=date(2025, 10, 1), description="Food", postings=postings1)
        
        # Transaction 2: Salary -> Checking
        postings2 = (
            Posting(account_id=salary.id, amount=Money(Decimal("-100.00"), "BRL")),
            Posting(account_id=checking.id, amount=Money(Decimal("100.00"), "BRL")),
        )
        tx2 = Transaction.create(date=date(2025, 10, 2), description="Salary", postings=postings2)
        
        with uow_with_transactions:
            uow_with_transactions.transactions.add(tx1)
            uow_with_transactions.transactions.add(tx2)
            uow_with_transactions.commit()
        
        # Act
        with uow_with_transactions:
            checking_txs = uow_with_transactions.transactions.find_by_account(checking.id)
            food_txs = uow_with_transactions.transactions.find_by_account(food.id)
        
        # Assert
        assert len(checking_txs) == 2  # Both transactions affect checking
        assert len(food_txs) == 1  # Only tx1 affects food
    
    @pytest.mark.skip(reason="JSON path query needs PostgreSQL-specific implementation")
    def test_find_by_tags(self, uow_with_transactions, sample_accounts):
        """Test finding transactions by tags."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        postings = (
            Posting(account_id=checking.id, amount=Money(Decimal("-15.00"), "BRL")),
            Posting(account_id=food.id, amount=Money(Decimal("15.00"), "BRL")),
        )
        
        tx1 = Transaction.create(
            date=date(2025, 10, 1),
            description="Pizza",
            postings=postings,
            tags=["food", "restaurant"]
        )
        
        tx2 = Transaction.create(
            date=date(2025, 10, 2),
            description="Supermarket",
            postings=postings,
            tags=["food", "essential"]
        )
        
        with uow_with_transactions:
            uow_with_transactions.transactions.add(tx1)
            uow_with_transactions.transactions.add(tx2)
            uow_with_transactions.commit()
        
        # Act - Find with "restaurant" OR "essential"
        with uow_with_transactions:
            found = uow_with_transactions.transactions.find_by_tags(["restaurant", "essential"])
        
        # Assert
        assert len(found) == 2  # Both match
    
    def test_search_description(self, uow_with_transactions, sample_accounts):
        """Test searching transactions by description text."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        postings = (
            Posting(account_id=checking.id, amount=Money(Decimal("-10.00"), "BRL")),
            Posting(account_id=food.id, amount=Money(Decimal("10.00"), "BRL")),
        )
        
        tx1 = Transaction.create(date=date(2025, 10, 1), description="Restaurant XYZ", postings=postings)
        tx2 = Transaction.create(date=date(2025, 10, 2), description="Supermarket ABC", postings=postings)
        
        with uow_with_transactions:
            uow_with_transactions.transactions.add(tx1)
            uow_with_transactions.transactions.add(tx2)
            uow_with_transactions.commit()
        
        # Act
        with uow_with_transactions:
            found = uow_with_transactions.transactions.search_description("restaurant")
        
        # Assert
        assert len(found) == 1
        assert "Restaurant" in found[0].description
    
    def test_list_all_with_limit(self, uow_with_transactions, sample_accounts):
        """Test listing all transactions with limit."""
        # Arrange - Create 5 transactions
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        for i in range(5):
            postings = (
                Posting(account_id=checking.id, amount=Money(Decimal("-10.00"), "BRL")),
                Posting(account_id=food.id, amount=Money(Decimal("10.00"), "BRL")),
            )
            tx = Transaction.create(
                date=date(2025, 10, i + 1),
                description=f"Transaction {i+1}",
                postings=postings,
            )
            with uow_with_transactions:
                uow_with_transactions.transactions.add(tx)
                uow_with_transactions.commit()
        
        # Act
        with uow_with_transactions:
            all_txs = uow_with_transactions.transactions.list_all()
            limited = uow_with_transactions.transactions.list_all(limit=3)
        
        # Assert
        assert len(all_txs) == 5
        assert len(limited) == 3
    
    def test_count_transactions(self, uow_with_transactions, sample_accounts):
        """Test counting transactions."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        for i in range(3):
            postings = (
                Posting(account_id=checking.id, amount=Money(Decimal("-10.00"), "BRL")),
                Posting(account_id=food.id, amount=Money(Decimal("10.00"), "BRL")),
            )
            tx = Transaction.create(
                date=date(2025, 10, i + 1),
                description=f"Transaction {i+1}",
                postings=postings,
            )
            with uow_with_transactions:
                uow_with_transactions.transactions.add(tx)
                uow_with_transactions.commit()
        
        # Act
        with uow_with_transactions:
            total = uow_with_transactions.transactions.count()
        
        # Assert
        assert total == 3
    
    def test_delete_transaction(self, uow_with_transactions, sample_accounts, session):
        """Test deleting a transaction."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        postings = (
            Posting(account_id=checking.id, amount=Money(Decimal("-10.00"), "BRL")),
            Posting(account_id=food.id, amount=Money(Decimal("10.00"), "BRL")),
        )
        
        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="To delete",
            postings=postings,
        )
        
        with uow_with_transactions:
            uow_with_transactions.transactions.add(transaction)
            uow_with_transactions.commit()
        
        transaction_id = transaction.id
        
        # Act
        with uow_with_transactions:
            uow_with_transactions.transactions.delete(transaction_id)
            uow_with_transactions.commit()
        
        # Assert
        db_transaction = session.query(TransactionModel).filter_by(id=transaction_id).first()
        assert db_transaction is None
        
        with pytest.raises(TransactionNotFoundError):
            with uow_with_transactions:
                uow_with_transactions.transactions.get(transaction_id)


class TestTransactionMapperIntegration:
    """Integration tests focusing on mapper behavior with complex aggregates."""
    
    def test_mapper_preserves_decimal_precision(self, uow_with_transactions, sample_accounts):
        """Test that Decimal precision is preserved in postings."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        
        postings = (
            Posting(account_id=checking.id, amount=Money(Decimal("-123.4567"), "BRL")),
            Posting(account_id=food.id, amount=Money(Decimal("123.4567"), "BRL")),
        )
        
        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Precision test",
            postings=postings,
        )
        
        # Act
        with uow_with_transactions:
            uow_with_transactions.transactions.add(transaction)
            uow_with_transactions.commit()
        
        # Assert
        with uow_with_transactions:
            retrieved = uow_with_transactions.transactions.get(transaction.id)
        
        assert retrieved.postings[0].amount.amount == Decimal("-123.4567")
        assert retrieved.postings[1].amount.amount == Decimal("123.4567")
    
    def test_mapper_handles_multiple_postings(self, uow_with_transactions, sample_accounts):
        """Test transaction with more than 2 postings (split transactions)."""
        # Arrange
        checking = sample_accounts["checking"]
        food = sample_accounts["food"]
        salary = sample_accounts["salary"]
        
        # Split: Checking pays for Food and Salary income
        postings = (
            Posting(account_id=checking.id, amount=Money(Decimal("-100.00"), "BRL")),
            Posting(account_id=food.id, amount=Money(Decimal("30.00"), "BRL")),
            Posting(account_id=salary.id, amount=Money(Decimal("70.00"), "BRL")),
        )
        
        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Split transaction",
            postings=postings,
        )
        
        # Act
        with uow_with_transactions:
            uow_with_transactions.transactions.add(transaction)
            uow_with_transactions.commit()
        
        # Assert
        with uow_with_transactions:
            retrieved = uow_with_transactions.transactions.get(transaction.id)
        
        assert len(retrieved.postings) == 3
        assert retrieved.is_balanced()
