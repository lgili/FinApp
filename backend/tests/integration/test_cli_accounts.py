"""Integration tests for CLI accounts commands.

Tests the complete flow from CLI command to database persistence
using the DI container and use cases.
"""

import pytest
from typer.testing import CliRunner

from finlite.interfaces.cli.app import app
from finlite.shared.di.container import create_container, init_database


@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def test_container():
    """Create test container with in-memory database."""
    container = create_container("sqlite:///:memory:")
    init_database(container)
    return container


@pytest.fixture(autouse=True)
def setup_test_container(test_container, monkeypatch):
    """Inject test container into CLI commands."""
    import sys
    
    # Get the actual app module (not the re-exported app object)
    app_module = sys.modules.get('finlite.interfaces.cli.app')
    if not app_module:
        # Force import
        import finlite.interfaces.cli.app as app_module
    
    # Store original
    original_container = app_module._container
    
    # Set test container (bypass get_container by directly setting _container)
    app_module._container = test_container
    
    yield
    
    # Restore
    app_module._container = original_container


class TestAccountsCreate:
    """Tests for 'fin accounts create' command."""
    
    def test_create_account_success(self, cli_runner):
        """Test creating an account successfully."""
        result = cli_runner.invoke(
            app,
            ["accounts", "create", "-c", "TEST001", "-n", "Test Account", "-t", "ASSET"]
        )
        
        assert result.exit_code == 0
        assert "✅ Account created successfully!" in result.stdout
        assert "TEST001" in result.stdout
        assert "ASSET" in result.stdout
    
    def test_create_account_with_currency(self, cli_runner):
        """Test creating account with custom currency."""
        result = cli_runner.invoke(
            app,
            ["accounts", "create", "-c", "BRL001", "-n", "Brazilian Account", "-t", "ASSET", "--currency", "BRL"]
        )
        
        assert result.exit_code == 0
        assert "✅ Account created successfully!" in result.stdout
        assert "BRL" in result.stdout
    
    def test_create_duplicate_account_fails(self, cli_runner):
        """Test that creating duplicate account fails."""
        # Create first account
        cli_runner.invoke(
            app,
            ["accounts", "create", "-c", "DUP001", "-n", "Duplicate", "-t", "ASSET"]
        )
        
        # Try to create duplicate
        result = cli_runner.invoke(
            app,
            ["accounts", "create", "-c", "DUP001", "-n", "Duplicate 2", "-t", "EXPENSE"]
        )
        
        assert result.exit_code == 1
        assert "❌" in result.stdout or "already exists" in result.stdout.lower()
    
    def test_create_account_invalid_type(self, cli_runner):
        """Test creating account with invalid type."""
        result = cli_runner.invoke(
            app,
            ["accounts", "create", "-c", "BAD001", "-n", "Bad Type", "-t", "INVALID"]
        )
        
        # Typer will catch this as invalid enum before reaching use case
        assert result.exit_code != 0


class TestAccountsList:
    """Tests for 'fin accounts list' command."""
    
    def test_list_empty_accounts(self, cli_runner):
        """Test listing when no accounts exist."""
        result = cli_runner.invoke(app, ["accounts", "list"])
        
        assert result.exit_code == 0
        assert "No accounts found" in result.stdout
    
    def test_list_multiple_accounts(self, cli_runner):
        """Test listing multiple accounts."""
        # Create accounts
        cli_runner.invoke(app, ["accounts", "create", "-c", "ACC001", "-n", "Account 1", "-t", "ASSET"])
        cli_runner.invoke(app, ["accounts", "create", "-c", "ACC002", "-n", "Account 2", "-t", "EXPENSE"])
        
        # List all
        result = cli_runner.invoke(app, ["accounts", "list"])
        
        assert result.exit_code == 0
        assert "ACC001" in result.stdout
        assert "ACC002" in result.stdout
        assert "ASSET" in result.stdout
        assert "EXPENSE" in result.stdout
    
    def test_list_filter_by_type(self, cli_runner):
        """Test filtering accounts by type."""
        # Create different types
        cli_runner.invoke(app, ["accounts", "create", "-c", "AST001", "-n", "Asset", "-t", "ASSET"])
        cli_runner.invoke(app, ["accounts", "create", "-c", "EXP001", "-n", "Expense", "-t", "EXPENSE"])
        
        # Filter by ASSET
        result = cli_runner.invoke(app, ["accounts", "list", "--type", "ASSET"])
        
        assert result.exit_code == 0
        assert "AST001" in result.stdout
        assert "EXP001" not in result.stdout


class TestAccountsBalance:
    """Tests for 'fin accounts balance' command."""
    
    def test_balance_account_not_found(self, cli_runner):
        """Test balance for non-existent account."""
        result = cli_runner.invoke(app, ["accounts", "balance", "NOTFOUND"])
        
        assert result.exit_code == 1
        assert "❌" in result.stdout or "not found" in result.stdout.lower()
    
    def test_balance_no_transactions(self, cli_runner):
        """Test balance for account with no transactions."""
        # Create account
        cli_runner.invoke(app, ["accounts", "create", "-c", "ZERO001", "-n", "Zero Balance", "-t", "ASSET"])
        
        # Check balance
        result = cli_runner.invoke(app, ["accounts", "balance", "ZERO001"])
        
        assert result.exit_code == 0
        assert "ZERO001" in result.stdout
        assert "Balance: 0" in result.stdout or "Balance: 0.0" in result.stdout
    
    def test_balance_with_transactions(self, cli_runner, test_container):
        """Test balance calculation with transactions."""
        # Create accounts
        cli_runner.invoke(app, ["accounts", "create", "-c", "CASH001", "-n", "Cash", "-t", "ASSET"])
        cli_runner.invoke(app, ["accounts", "create", "-c", "INC001", "-n", "Income", "-t", "INCOME"])
        
        # Create transaction directly via use case (since interactive CLI is hard to test)
        from finlite.application.dtos import CreateTransactionDTO, CreatePostingDTO
        from decimal import Decimal
        from datetime import datetime
        
        use_case = test_container.record_transaction_use_case()
        dto = CreateTransactionDTO(
            description="Test transaction",
            date=datetime(2025, 1, 15),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="CASH001", amount=Decimal("100"), currency="USD"),
                CreatePostingDTO(account_code="INC001", amount=Decimal("-100"), currency="USD"),
            ]
        )
        use_case.execute(dto)
        
        # Check balance
        result = cli_runner.invoke(app, ["accounts", "balance", "CASH001"])
        
        assert result.exit_code == 0
        assert "CASH001" in result.stdout
        assert "100" in result.stdout


class TestAccountsHelp:
    """Tests for help commands."""
    
    def test_accounts_help(self, cli_runner):
        """Test accounts help command."""
        result = cli_runner.invoke(app, ["accounts", "--help"])
        
        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "list" in result.stdout
        assert "balance" in result.stdout
    
    def test_accounts_create_help(self, cli_runner):
        """Test accounts create help."""
        result = cli_runner.invoke(app, ["accounts", "create", "--help"])
        
        assert result.exit_code == 0
        assert "--code" in result.stdout
        assert "--name" in result.stdout
        assert "--type" in result.stdout
