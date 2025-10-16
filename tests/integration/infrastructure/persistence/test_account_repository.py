"""
Integration tests for SqlAlchemyAccountRepository.

These tests validate:
- Domain Entity → Mapper → ORM Model → Database
- Database → ORM Model → Mapper → Domain Entity
- CRUD operations through repository pattern
- UnitOfWork transaction management
"""
import pytest
from uuid import uuid4
from decimal import Decimal

from finlite.domain.entities.account import Account
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.exceptions import AccountNotFoundError
from finlite.infrastructure.persistence.sqlalchemy.repositories.account_repository import (
    SqlAlchemyAccountRepository
)
from finlite.infrastructure.persistence.sqlalchemy.models import AccountModel
from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import uuid_to_int, int_to_uuid


class TestSqlAlchemyAccountRepository:
    """Integration tests for Account repository."""
    
    def test_add_account_persists_to_database(self, uow, session):
        """Test that adding an account persists it to the database."""
        # Arrange
        account = Account.create(
            code="Assets:Checking",
            name="Checking Account",
            account_type=AccountType.ASSET,
            currency="BRL"
        )
        
        # Act
        with uow:
            uow.accounts.add(account)
            uow.commit()
        
        # Assert - Query directly from DB to verify persistence
        db_account = session.query(AccountModel).filter_by(name="Checking Account").first()
        assert db_account is not None
        assert db_account.name == "Checking Account"
        assert db_account.type == "ASSET"
        assert db_account.currency == "BRL"
    
    def test_get_account_retrieves_from_database(self, uow, session):
        """Test that getting an account retrieves it from the database."""
        # Arrange - Insert directly into DB
        account_id = uuid4()
        int_id = uuid_to_int(account_id)
        db_account = AccountModel(
            id=int_id,
            name="Savings Account",
            code="Assets:Savings",  # Store account code
            type="ASSET",
            currency="BRL"
        )
        session.add(db_account)
        session.commit()

        # Act - retrieve by the original UUID
        with uow:
            account = uow.accounts.get(account_id)

        # Assert - Verify domain entity
        # Note: UUID is reconstructed from integer ID, so verify it matches
        from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import int_to_uuid
        expected_uuid = int_to_uuid(int_id)

        assert account is not None
        assert account.id == expected_uuid
        assert account.code == "Assets:Savings"
        assert account.name == "Savings Account"
        assert account.account_type == AccountType.ASSET
        assert account.currency == "BRL"
    
    def test_get_nonexistent_account_raises_error(self, uow):
        """Test that getting a non-existent account raises AccountNotFoundError."""
        nonexistent_id = uuid4()
        
        with pytest.raises(AccountNotFoundError) as exc_info:
            with uow:
                uow.accounts.get(nonexistent_id)
        
        assert str(nonexistent_id) in str(exc_info.value)
    
    def test_find_by_name_returns_account(self, uow):
        """Test finding account by exact name."""
        # Arrange
        account = Account.create(
            code="Assets:Bank",
            name="Bank Account",
            account_type=AccountType.ASSET,
            currency="BRL"
        )
        
        with uow:
            uow.accounts.add(account)
            uow.commit()
        
        # Act
        with uow:
            found = uow.accounts.find_by_name("Bank Account")
        
        # Assert
        assert found is not None
        assert found.name == "Bank Account"
    
    def test_find_by_type_returns_matching_accounts(self, uow):
        """Test finding accounts by type."""
        # Arrange
        accounts = [
            Account.create(code="Assets:Checking", name="Checking", account_type=AccountType.ASSET, currency="BRL"),
            Account.create(code="Liabilities:CreditCard", name="Credit Card", account_type=AccountType.LIABILITY, currency="BRL"),
            Account.create(code="Assets:Savings", name="Savings", account_type=AccountType.ASSET, currency="BRL"),
            Account.create(code="Income:Revenue", name="Revenue", account_type=AccountType.INCOME, currency="BRL"),
        ]
        
        with uow:
            for account in accounts:
                uow.accounts.add(account)
            uow.commit()
        
        # Act
        with uow:
            assets = uow.accounts.find_by_type(AccountType.ASSET)
        
        # Assert
        assert len(assets) == 2
        assert all(acc.account_type == AccountType.ASSET for acc in assets)
    
    def test_list_all_returns_all_active_accounts(self, uow, session):
        """Test listing all active accounts."""
        # Arrange
        accounts = [
            Account.create(code="Assets:Account1", name="Account 1", account_type=AccountType.ASSET, currency="BRL"),
            Account.create(code="Liabilities:Account2", name="Account 2", account_type=AccountType.LIABILITY, currency="BRL"),
            Account.create(code="Equity:Account3", name="Account 3", account_type=AccountType.EQUITY, currency="BRL"),
        ]
        
        with uow:
            for account in accounts:
                uow.accounts.add(account)
            uow.commit()
        
        # Mark one as inactive directly in DB
        db_account = session.query(AccountModel).filter_by(name="Account 2").first()
        db_account.is_archived = True  # Mark as archived (inactive)
        session.commit()
        
        # Act
        with uow:
            all_accounts = uow.accounts.list_all(include_inactive=True)
            active_only = uow.accounts.list_all(include_inactive=False)
        
        # Assert
        assert len(all_accounts) == 3
        assert len(active_only) == 2
        assert all(acc.is_active for acc in active_only)
    
    def test_exists_returns_true_for_existing_account(self, uow):
        """Test exists method returns True for existing account."""
        # Arrange
        account = Account.create(code="Assets:Test", name="Test Account", account_type=AccountType.ASSET, currency="BRL")
        
        with uow:
            uow.accounts.add(account)
            uow.commit()
        
        # Act & Assert
        with uow:
            assert uow.accounts.exists(account.id) is True
            assert uow.accounts.exists(uuid4()) is False
    
    def test_update_modifies_existing_account(self, uow):
        """Test updating an account modifies it in the database."""
        # Arrange
        account = Account.create(
            code="Assets:Original",
            name="Original Name",
            account_type=AccountType.ASSET,
            currency="BRL"
        )
        
        with uow:
            uow.accounts.add(account)
            uow.commit()
        
        # Act - Modify and update
        account.rename("Updated Name")
        
        with uow:
            uow.accounts.update(account)
            uow.commit()
        
        # Assert - Retrieve and verify
        with uow:
            updated = uow.accounts.get(account.id)
        
        assert updated.name == "Updated Name"
    
    def test_delete_removes_account_from_database(self, uow, session):
        """Test deleting an account removes it from the database."""
        # Arrange
        account = Account.create(code="Assets:Delete", name="To Delete", account_type=AccountType.ASSET, currency="BRL")
        
        with uow:
            uow.accounts.add(account)
            uow.commit()
        
        account_id = account.id
        
        # Act
        with uow:
            uow.accounts.delete(account_id)
            uow.commit()
        
        # Assert - Verify it's gone
        db_account = session.query(AccountModel).filter_by(id=account_id).first()
        assert db_account is None
        
        with pytest.raises(AccountNotFoundError):
            with uow:
                uow.accounts.get(account_id)
    
    def test_rollback_undoes_changes(self, uow, session):
        """Test that rollback undoes uncommitted changes."""
        # Arrange
        account = Account.create(code="Assets:Rollback", name="Test Rollback", account_type=AccountType.ASSET, currency="BRL")
        
        # Act - Add but don't commit
        with uow:
            uow.accounts.add(account)
            # Rollback happens automatically when context exits without commit
        
        # Assert - Account should not exist
        db_account = session.query(AccountModel).filter_by(id=account.id).first()
        assert db_account is None
    
    def test_account_with_parent_hierarchy(self, uow):
        """Test persisting account with parent-child relationship."""
        # Arrange
        parent = Account.create(code="Assets:Parent", name="Parent Account", account_type=AccountType.ASSET, currency="BRL")
        child = Account.create(
            code="Assets:Parent:Child",
            name="Child Account",
            account_type=AccountType.ASSET,
            currency="BRL",
            parent_id=parent.id
        )

        # Act
        with uow:
            uow.accounts.add(parent)
            uow.accounts.add(child)
            uow.commit()

        # Assert
        # Note: After persistence, both parent and child IDs are regenerated from integer IDs
        with uow:
            retrieved_child = uow.accounts.get(child.id)
            retrieved_parent = uow.accounts.get(parent.id)

        # Parent ID should match the retrieved parent's ID
        assert retrieved_child.parent_id == retrieved_parent.id


class TestAccountMapperIntegration:
    """Integration tests focusing on mapper behavior."""
    
    def test_mapper_handles_all_account_types(self, uow):
        """Test that mapper correctly handles all AccountType enum values."""
        account_types = [
            AccountType.ASSET,
            AccountType.LIABILITY,
            AccountType.EQUITY,
            AccountType.INCOME,
            AccountType.EXPENSE,
        ]

        accounts = []
        for acc_type in account_types:
            account = Account.create(
                code=f"{acc_type.value}:Test",
                name=f"{acc_type.value} Account",
                account_type=acc_type,
                currency="BRL"
            )
            accounts.append(account)
        
        # Act - Persist all
        with uow:
            for account in accounts:
                uow.accounts.add(account)
            uow.commit()
        
        # Assert - Retrieve all and verify types
        with uow:
            for account in accounts:
                retrieved = uow.accounts.get(account.id)
                assert retrieved.account_type == account.account_type
    
    def test_mapper_preserves_currency_precision(self, uow):
        """Test that currency is preserved through the full stack."""
        # Arrange
        account = Account.create(
            code="Assets:USD",
            name="USD Account",
            account_type=AccountType.ASSET,
            currency="USD"
        )
        
        # Act
        with uow:
            uow.accounts.add(account)
            uow.commit()
        
        # Assert
        with uow:
            retrieved = uow.accounts.get(account.id)
        
        assert retrieved.currency == "USD"
