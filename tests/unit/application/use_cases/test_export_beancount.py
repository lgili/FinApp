"""Tests for ExportBeancountUseCase."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from finlite.application.use_cases.export_beancount import (
    ExportBeancountCommand,
    ExportBeancountResult,
    ExportBeancountUseCase,
)
from finlite.domain.entities.account import Account
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting


class TestExportBeancountUseCase:
    """Tests for ExportBeancountUseCase."""

    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work."""
        uow = Mock()
        uow.__enter__ = Mock(return_value=uow)
        uow.__exit__ = Mock(return_value=False)
        return uow

    @pytest.fixture
    def mock_account_repository(self):
        """Mock Account Repository."""
        return Mock()

    @pytest.fixture
    def mock_transaction_repository(self):
        """Mock Transaction Repository."""
        return Mock()

    @pytest.fixture
    def use_case(
        self, mock_uow, mock_account_repository, mock_transaction_repository
    ):
        """Create use case instance."""
        return ExportBeancountUseCase(
            uow=mock_uow,
            account_repository=mock_account_repository,
            transaction_repository=mock_transaction_repository,
        )

    @pytest.fixture
    def temp_output_file(self):
        """Create temporary output file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".beancount", delete=False) as f:
            yield Path(f.name)
            # Cleanup
            Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def checking_account(self):
        """Create checking account."""
        return Account.create(
            code="Assets:Bank:Checking",
            name="Checking Account",
            account_type=AccountType.ASSET,
            currency="USD",
        )

    @pytest.fixture
    def salary_account(self):
        """Create salary income account."""
        return Account.create(
            code="Income:Salary",
            name="Salary",
            account_type=AccountType.INCOME,
            currency="USD",
        )

    @pytest.fixture
    def groceries_account(self):
        """Create groceries expense account."""
        return Account.create(
            code="Expenses:Groceries",
            name="Groceries",
            account_type=AccountType.EXPENSE,
            currency="USD",
        )

    def test_export_empty_ledger(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
    ):
        """Successfully exports empty ledger."""
        mock_account_repository.list_all.return_value = []
        mock_transaction_repository.list_all.return_value = []

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file, operating_currency="USD"
            )
        )

        assert isinstance(result, ExportBeancountResult)
        assert result.accounts_count == 0
        assert result.transactions_count == 0
        assert result.output_path.exists()
        assert result.file_size_bytes > 0

        # Check file contents
        content = result.output_path.read_text()
        assert "Beancount Ledger" in content
        assert 'option "operating_currency" "USD"' in content

    def test_export_accounts_only(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
        checking_account,
        salary_account,
    ):
        """Exports account declarations."""
        mock_account_repository.list_all.return_value = [
            checking_account,
            salary_account,
        ]
        mock_transaction_repository.list_all.return_value = []

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file, operating_currency="USD"
            )
        )

        assert result.accounts_count == 2
        assert result.transactions_count == 0

        content = result.output_path.read_text()
        assert "Assets:Bank:Checking" in content
        assert "Income:Salary" in content
        assert "open Assets:Bank:Checking USD" in content
        assert "open Income:Salary USD" in content

    def test_export_single_transaction(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
        checking_account,
        salary_account,
    ):
        """Exports single transaction."""
        transaction = Transaction.create(
            date=datetime(2025, 10, 1).date(),
            description="Monthly Salary",
            postings=[
                Posting(checking_account.id, Money.from_float(5000.0, "USD")),
                Posting(salary_account.id, Money.from_float(-5000.0, "USD")),
            ],
        )

        mock_account_repository.list_all.return_value = [
            checking_account,
            salary_account,
        ]
        mock_transaction_repository.list_all.return_value = [transaction]

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file, operating_currency="USD"
            )
        )

        assert result.transactions_count == 1

        content = result.output_path.read_text()
        assert "2025-10-01 * \"Monthly Salary\"" in content
        assert "Assets:Bank:Checking" in content
        assert "Income:Salary" in content
        assert "5000.00 USD" in content
        assert "-5000.00 USD" in content

    def test_export_multiple_transactions(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
        checking_account,
        salary_account,
        groceries_account,
    ):
        """Exports multiple transactions in chronological order."""
        tx1 = Transaction.create(
            date=datetime(2025, 10, 1).date(),
            description="Salary",
            postings=[
                Posting(checking_account.id, Money.from_float(5000.0, "USD")),
                Posting(salary_account.id, Money.from_float(-5000.0, "USD")),
            ],
        )

        tx2 = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Groceries",
            postings=[
                Posting(checking_account.id, Money.from_float(-150.0, "USD")),
                Posting(groceries_account.id, Money.from_float(150.0, "USD")),
            ],
        )

        mock_account_repository.list_all.return_value = [
            checking_account,
            salary_account,
            groceries_account,
        ]
        mock_transaction_repository.list_all.return_value = [tx2, tx1]  # Reversed order

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file, operating_currency="USD"
            )
        )

        assert result.transactions_count == 2

        content = result.output_path.read_text()
        # Should be sorted by date
        salary_pos = content.find("2025-10-01")
        groceries_pos = content.find("2025-10-05")
        assert salary_pos < groceries_pos, "Transactions should be in chronological order"

    def test_export_with_tags(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
        checking_account,
        groceries_account,
    ):
        """Exports transactions with tags."""
        transaction = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Grocery shopping",
            postings=[
                Posting(checking_account.id, Money.from_float(-150.0, "USD")),
                Posting(groceries_account.id, Money.from_float(150.0, "USD")),
            ],
            tags=["essential", "food"],
        )

        mock_account_repository.list_all.return_value = [
            checking_account,
            groceries_account,
        ]
        mock_transaction_repository.list_all.return_value = [transaction]

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file,
                operating_currency="USD",
                include_metadata=True,
            )
        )

        content = result.output_path.read_text()
        assert "#essential" in content
        assert "#food" in content

    def test_export_without_metadata(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
        checking_account,
        groceries_account,
    ):
        """Skips metadata when include_metadata=False."""
        transaction = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Grocery shopping",
            postings=[
                Posting(checking_account.id, Money.from_float(-150.0, "USD")),
                Posting(groceries_account.id, Money.from_float(150.0, "USD")),
            ],
            tags=["essential", "food"],
        )

        mock_account_repository.list_all.return_value = [
            checking_account,
            groceries_account,
        ]
        mock_transaction_repository.list_all.return_value = [transaction]

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file,
                operating_currency="USD",
                include_metadata=False,
            )
        )

        content = result.output_path.read_text()
        assert "#essential" not in content
        assert "#food" not in content

    def test_export_date_range(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
        checking_account,
        salary_account,
        groceries_account,
    ):
        """Exports only transactions within date range."""
        tx_in_range = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description="Groceries",
            postings=[
                Posting(checking_account.id, Money.from_float(-150.0, "USD")),
                Posting(groceries_account.id, Money.from_float(150.0, "USD")),
            ],
        )

        tx_out_range = Transaction.create(
            date=datetime(2025, 9, 1).date(),
            description="Salary",
            postings=[
                Posting(checking_account.id, Money.from_float(5000.0, "USD")),
                Posting(salary_account.id, Money.from_float(-5000.0, "USD")),
            ],
        )

        mock_account_repository.list_all.return_value = [
            checking_account,
            salary_account,
            groceries_account,
        ]
        # Repository should return only filtered transactions
        mock_transaction_repository.find_by_date_range.return_value = [tx_in_range]

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file,
                operating_currency="USD",
                from_date=datetime(2025, 10, 1),
                to_date=datetime(2025, 10, 31),
            )
        )

        assert result.transactions_count == 1

        content = result.output_path.read_text()
        # Groceries transaction should be in transactions section
        assert "2025-10-05 * \"Groceries\"" in content
        # Salary transaction should NOT be in transactions section
        assert "2025-09-01 * \"Salary\"" not in content
        # But Salary account can still appear in account declarations
        assert "Income:Salary" in content  # Account declaration

    def test_export_escaped_quotes_in_description(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
        checking_account,
        groceries_account,
    ):
        """Escapes quotes in transaction description."""
        transaction = Transaction.create(
            date=datetime(2025, 10, 5).date(),
            description='Purchase at "Super Market"',
            postings=[
                Posting(checking_account.id, Money.from_float(-150.0, "USD")),
                Posting(groceries_account.id, Money.from_float(150.0, "USD")),
            ],
        )

        mock_account_repository.list_all.return_value = [
            checking_account,
            groceries_account,
        ]
        mock_transaction_repository.list_all.return_value = [transaction]

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file, operating_currency="USD"
            )
        )

        content = result.output_path.read_text()
        assert '\\"Super Market\\"' in content

    def test_export_creates_parent_directories(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
    ):
        """Creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "ledger.beancount"

            mock_account_repository.list_all.return_value = []
            mock_transaction_repository.list_all.return_value = []

            result = use_case.execute(
                ExportBeancountCommand(
                    output_path=output_path, operating_currency="USD"
                )
            )

            assert result.output_path.exists()
            assert result.output_path.parent.exists()

    def test_export_uses_account_currency(
        self,
        use_case,
        mock_account_repository,
        mock_transaction_repository,
        temp_output_file,
    ):
        """Uses account currency in open directive."""
        brl_account = Account.create(
            code="Assets:Bank:BRL",
            name="BRL Account",
            account_type=AccountType.ASSET,
            currency="BRL",
        )

        mock_account_repository.list_all.return_value = [brl_account]
        mock_transaction_repository.list_all.return_value = []

        result = use_case.execute(
            ExportBeancountCommand(
                output_path=temp_output_file, operating_currency="USD"
            )
        )

        content = result.output_path.read_text()
        assert "open Assets:Bank:BRL BRL" in content
