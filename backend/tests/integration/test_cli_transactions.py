"""Integration tests for CLI transactions commands.

Tests the complete flow from CLI command to database persistence
using the DI container and use cases.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from typer.testing import CliRunner

from finlite.interfaces.cli.app import app
from finlite.shared.di.container import create_container, init_database
from finlite.application.dtos import CreateTransactionDTO, CreatePostingDTO


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


@pytest.fixture
def sample_accounts(cli_runner):
    """Create sample accounts for testing transactions."""
    cli_runner.invoke(app, ["accounts", "create", "-c", "CASH", "-n", "Cash Account", "-t", "ASSET"])
    cli_runner.invoke(app, ["accounts", "create", "-c", "INCOME", "-n", "Income Account", "-t", "INCOME"])
    cli_runner.invoke(app, ["accounts", "create", "-c", "EXPENSE", "-n", "Expense Account", "-t", "EXPENSE"])
    cli_runner.invoke(app, ["accounts", "create", "-c", "BANK", "-n", "Bank Account", "-t", "ASSET"])


class TestTransactionsList:
    """Tests for 'fin transactions list' command."""
    
    def test_list_empty_transactions(self, cli_runner, sample_accounts):
        """Test listing when no transactions exist."""
        result = cli_runner.invoke(app, ["transactions", "list"])
        
        assert result.exit_code == 0
        assert "No transactions found" in result.stdout
    
    def test_list_multiple_transactions(self, cli_runner, sample_accounts, test_container):
        """Test listing multiple transactions."""
        # Create transactions via use case
        use_case = test_container.record_transaction_use_case()
        
        # Transaction 1
        dto1 = CreateTransactionDTO(
            description="Salary",
            date=datetime(2025, 1, 15),
            payee="Company XYZ",
            postings=[
                CreatePostingDTO(account_code="BANK", amount=Decimal("5000"), currency="USD"),
                CreatePostingDTO(account_code="INCOME", amount=Decimal("-5000"), currency="USD"),
            ]
        )
        use_case.execute(dto1)
        
        # Transaction 2
        dto2 = CreateTransactionDTO(
            description="Grocery shopping",
            date=datetime(2025, 1, 16),
            payee="Supermarket",
            postings=[
                CreatePostingDTO(account_code="EXPENSE", amount=Decimal("150"), currency="USD"),
                CreatePostingDTO(account_code="CASH", amount=Decimal("-150"), currency="USD"),
            ]
        )
        use_case.execute(dto2)
        
        # List all transactions (provide "n" to skip details)
        result = cli_runner.invoke(app, ["transactions", "list"], input="n\n")
        
        assert result.exit_code == 0
        assert "Salary" in result.stdout
        assert "Grocery shopping" in result.stdout
        assert "2025-01-15" in result.stdout
        assert "2025-01-16" in result.stdout
    
    def test_list_with_limit(self, cli_runner, sample_accounts, test_container):
        """Test listing with limit."""
        use_case = test_container.record_transaction_use_case()
        
        # Create 5 transactions
        for i in range(5):
            dto = CreateTransactionDTO(
                description=f"Transaction {i+1}",
                date=datetime(2025, 1, 10 + i),
                payee=None,
                postings=[
                    CreatePostingDTO(account_code="CASH", amount=Decimal("100"), currency="USD"),
                    CreatePostingDTO(account_code="INCOME", amount=Decimal("-100"), currency="USD"),
                ]
            )
            use_case.execute(dto)
        
        # List with limit of 3 (provide "n" to skip details)
        result = cli_runner.invoke(app, ["transactions", "list", "--limit", "3"], input="n\n")
        
        assert result.exit_code == 0
        # Should show "(3 results)" or similar
        assert "3" in result.stdout
    
    def test_list_filter_by_account(self, cli_runner, sample_accounts, test_container):
        """Test filtering transactions by account."""
        use_case = test_container.record_transaction_use_case()
        
        # Transaction with CASH
        dto1 = CreateTransactionDTO(
            description="Cash transaction",
            date=datetime(2025, 1, 15),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="CASH", amount=Decimal("100"), currency="USD"),
                CreatePostingDTO(account_code="INCOME", amount=Decimal("-100"), currency="USD"),
            ]
        )
        use_case.execute(dto1)
        
        # Transaction with BANK (not CASH)
        dto2 = CreateTransactionDTO(
            description="Bank transaction",
            date=datetime(2025, 1, 16),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="BANK", amount=Decimal("200"), currency="USD"),
                CreatePostingDTO(account_code="INCOME", amount=Decimal("-200"), currency="USD"),
            ]
        )
        use_case.execute(dto2)
        
        # Filter by CASH account (provide "n" to skip details)
        result = cli_runner.invoke(app, ["transactions", "list", "--account", "CASH"], input="n\n")
        
        assert result.exit_code == 0
        assert "Cash transaction" in result.stdout
        assert "Bank transaction" not in result.stdout
    
    def test_list_filter_by_date_range(self, cli_runner, sample_accounts, test_container):
        """Test filtering by date range."""
        use_case = test_container.record_transaction_use_case()
        
        # Transaction in January
        dto1 = CreateTransactionDTO(
            description="January transaction",
            date=datetime(2025, 1, 15),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="CASH", amount=Decimal("100"), currency="USD"),
                CreatePostingDTO(account_code="INCOME", amount=Decimal("-100"), currency="USD"),
            ]
        )
        use_case.execute(dto1)
        
        # Transaction in February
        dto2 = CreateTransactionDTO(
            description="February transaction",
            date=datetime(2025, 2, 15),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="CASH", amount=Decimal("200"), currency="USD"),
                CreatePostingDTO(account_code="INCOME", amount=Decimal("-200"), currency="USD"),
            ]
        )
        use_case.execute(dto2)
        
        # Filter January only (provide "n" to skip details)
        result = cli_runner.invoke(
            app, 
            ["transactions", "list", "--start", "2025-01-01", "--end", "2025-01-31"],
            input="n\n"
        )
        
        assert result.exit_code == 0
        assert "January transaction" in result.stdout
        assert "February transaction" not in result.stdout


class TestTransactionsCreate:
    """Tests for 'fin transactions create' command.
    
    Note: Interactive input testing is complex, so we test the command
    structure and error cases. Full flow is tested via use case.
    """
    
    def test_create_requires_description(self, cli_runner, sample_accounts):
        """Test that description is required."""
        result = cli_runner.invoke(app, ["transactions", "create"])
        
        # Should fail without description
        assert result.exit_code != 0
    
    def test_create_help(self, cli_runner):
        """Test create help command."""
        result = cli_runner.invoke(app, ["transactions", "create", "--help"])
        
        assert result.exit_code == 0
        assert "--description" in result.stdout
        assert "--date" in result.stdout
        assert "--payee" in result.stdout
        assert "interactive" in result.stdout.lower() or "posting" in result.stdout.lower()


class TestTransactionsIntegration:
    """Integration tests combining transactions and accounts."""
    
    def test_transaction_updates_account_balance(self, cli_runner, sample_accounts, test_container):
        """Test that creating transaction updates account balances."""
        # Check initial balance
        result = cli_runner.invoke(app, ["accounts", "balance", "CASH"])
        assert "Balance: 0" in result.stdout or "Balance: 0.0" in result.stdout
        
        # Create transaction
        use_case = test_container.record_transaction_use_case()
        dto = CreateTransactionDTO(
            description="Add cash",
            date=datetime(2025, 1, 15),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="CASH", amount=Decimal("1000"), currency="USD"),
                CreatePostingDTO(account_code="INCOME", amount=Decimal("-1000"), currency="USD"),
            ]
        )
        use_case.execute(dto)
        
        # Check updated balance
        result = cli_runner.invoke(app, ["accounts", "balance", "CASH"])
        assert result.exit_code == 0
        assert "1000" in result.stdout
    
    def test_multiple_transactions_cumulative_balance(self, cli_runner, sample_accounts, test_container):
        """Test that multiple transactions accumulate correctly."""
        use_case = test_container.record_transaction_use_case()
        
        # Transaction 1: +500
        dto1 = CreateTransactionDTO(
            description="Income 1",
            date=datetime(2025, 1, 10),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="CASH", amount=Decimal("500"), currency="USD"),
                CreatePostingDTO(account_code="INCOME", amount=Decimal("-500"), currency="USD"),
            ]
        )
        use_case.execute(dto1)
        
        # Transaction 2: +300
        dto2 = CreateTransactionDTO(
            description="Income 2",
            date=datetime(2025, 1, 11),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="CASH", amount=Decimal("300"), currency="USD"),
                CreatePostingDTO(account_code="INCOME", amount=Decimal("-300"), currency="USD"),
            ]
        )
        use_case.execute(dto2)
        
        # Transaction 3: -200 (expense)
        dto3 = CreateTransactionDTO(
            description="Expense",
            date=datetime(2025, 1, 12),
            payee=None,
            postings=[
                CreatePostingDTO(account_code="EXPENSE", amount=Decimal("200"), currency="USD"),
                CreatePostingDTO(account_code="CASH", amount=Decimal("-200"), currency="USD"),
            ]
        )
        use_case.execute(dto3)
        
        # Check final balance: 500 + 300 - 200 = 600
        result = cli_runner.invoke(app, ["accounts", "balance", "CASH"])
        assert result.exit_code == 0
        assert "600" in result.stdout


class TestTransactionsHelp:
    """Tests for help commands."""
    
    def test_transactions_help(self, cli_runner):
        """Test transactions help command."""
        result = cli_runner.invoke(app, ["transactions", "--help"])
        
        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "list" in result.stdout
    
    def test_transactions_list_help(self, cli_runner):
        """Test transactions list help."""
        result = cli_runner.invoke(app, ["transactions", "list", "--help"])
        
        assert result.exit_code == 0
        assert "--account" in result.stdout
        assert "--start" in result.stdout
        assert "--end" in result.stdout
        assert "--limit" in result.stdout
