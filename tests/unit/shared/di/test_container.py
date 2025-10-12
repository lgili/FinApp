"""Unit tests for Dependency Injection Container."""

import pytest
from sqlalchemy import text

from finlite.shared.di import Container, create_container, init_database
from finlite.application.use_cases import (
    CreateAccountUseCase,
    RecordTransactionUseCase,
    ListAccountsUseCase,
    GetAccountBalanceUseCase,
    ListTransactionsUseCase,
)


class TestContainer:
    """Test suite for DI Container."""

    @pytest.fixture
    def container(self):
        """Create container with in-memory database."""
        container = create_container("sqlite:///:memory:", echo=False)
        init_database(container)
        yield container
        # Cleanup
        container.database_engine().dispose()

    def test_container_creation(self, container):
        """Test that container is created successfully."""
        assert container is not None
        assert hasattr(container, 'config')
        assert hasattr(container, 'database_engine')

    def test_database_engine_creation(self, container):
        """Test that database engine is created."""
        engine = container.database_engine()
        assert engine is not None
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_session_factory_creation(self, container):
        """Test that session factory is created."""
        session_factory = container.session_factory()
        assert session_factory is not None
        
        # Test session creation
        session = session_factory()
        assert session is not None
        session.close()

    def test_mappers_creation(self, container):
        """Test that mappers are created."""
        account_mapper = container.account_mapper()
        transaction_mapper = container.transaction_mapper()
        
        assert account_mapper is not None
        assert transaction_mapper is not None

    def test_repositories_creation(self, container):
        """Test that repositories are created."""
        account_repo = container.account_repository()
        transaction_repo = container.transaction_repository()
        
        assert account_repo is not None
        assert transaction_repo is not None

    def test_unit_of_work_creation(self, container):
        """Test that UnitOfWork is created."""
        uow = container.unit_of_work()
        assert uow is not None

    def test_create_account_use_case(self, container):
        """Test that CreateAccountUseCase is wired correctly."""
        use_case = container.create_account_use_case()
        
        assert isinstance(use_case, CreateAccountUseCase)
        assert use_case._uow is not None

    def test_record_transaction_use_case(self, container):
        """Test that RecordTransactionUseCase is wired correctly."""
        use_case = container.record_transaction_use_case()
        
        assert isinstance(use_case, RecordTransactionUseCase)
        assert use_case._uow is not None

    def test_list_accounts_use_case(self, container):
        """Test that ListAccountsUseCase is wired correctly."""
        use_case = container.list_accounts_use_case()
        
        assert isinstance(use_case, ListAccountsUseCase)
        assert use_case._uow is not None

    def test_get_account_balance_use_case(self, container):
        """Test that GetAccountBalanceUseCase is wired correctly."""
        use_case = container.get_account_balance_use_case()
        
        assert isinstance(use_case, GetAccountBalanceUseCase)
        assert use_case._uow is not None

    def test_list_transactions_use_case(self, container):
        """Test that ListTransactionsUseCase is wired correctly."""
        use_case = container.list_transactions_use_case()
        
        assert isinstance(use_case, ListTransactionsUseCase)
        assert use_case._uow is not None

    def test_use_cases_have_different_instances(self, container):
        """Test that each call to use_case provider creates new instance."""
        use_case1 = container.create_account_use_case()
        use_case2 = container.create_account_use_case()
        
        # Factory provider should create different instances
        assert use_case1 is not use_case2

    def test_mappers_are_singletons(self, container):
        """Test that mappers are singletons."""
        mapper1 = container.account_mapper()
        mapper2 = container.account_mapper()
        
        # Singleton provider should return same instance
        assert mapper1 is mapper2

    def test_database_tables_created(self, container):
        """Test that database tables are created."""
        engine = container.database_engine()
        
        # Check that tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "accounts" in tables
        assert "transactions" in tables
        assert "postings" in tables


class TestContainerIntegration:
    """Integration tests for DI Container with actual database operations."""

    @pytest.fixture
    def container(self):
        """Create container with in-memory database."""
        container = create_container("sqlite:///:memory:", echo=False)
        init_database(container)
        yield container
        container.database_engine().dispose()

    def test_end_to_end_create_account(self, container):
        """Test creating account through DI container end-to-end."""
        from finlite.application.dtos import CreateAccountDTO
        
        # Get use case from container
        use_case = container.create_account_use_case()
        
        # Create account
        dto = CreateAccountDTO(
            code="ASSET001",  # Using numeric code instead
            name="Test Account",
            type="ASSET",
            currency="USD",
        )
        
        result = use_case.execute(dto)
        
        # Assert
        assert result.created is True
        assert result.account.code == "ASSET001"
        assert result.account.currency == "USD"

    def test_end_to_end_list_accounts(self, container):
        """Test listing accounts through DI container."""
        from finlite.application.dtos import CreateAccountDTO
        
        # Create some accounts first
        create_use_case = container.create_account_use_case()
        create_use_case.execute(
            CreateAccountDTO(
                code="ASSET001",
                name="Account 1",
                type="ASSET",
                currency="USD",
            )
        )
        create_use_case.execute(
            CreateAccountDTO(
                code="EXPENSE001",
                name="Account 2",
                type="EXPENSE",
                currency="USD",
            )
        )
        
        # List accounts
        list_use_case = container.list_accounts_use_case()
        accounts = list_use_case.execute()
        
        # Assert
        assert len(accounts) == 2
        assert any(acc.code == "ASSET001" for acc in accounts)
        assert any(acc.code == "EXPENSE001" for acc in accounts)
