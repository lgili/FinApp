"""Tests for PostPendingEntriesUseCase."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from finlite.application.use_cases.post_pending_entries import (
    PostPendingEntriesCommand,
    PostPendingEntriesResult,
    PostPendingEntriesUseCase,
)
from finlite.config import Settings
from finlite.domain.entities.account import Account
from finlite.domain.entities.statement_entry import StatementEntry
from finlite.domain.value_objects.account_type import AccountType


class TestPostPendingEntriesUseCase:
    """Tests for PostPendingEntriesUseCase."""

    @pytest.fixture
    def mock_uow(self):
        """Mock Unit of Work."""
        uow = Mock()
        uow.__enter__ = Mock(return_value=uow)
        uow.__exit__ = Mock(return_value=False)
        uow.commit = Mock()
        return uow

    @pytest.fixture
    def mock_account_repository(self):
        """Mock Account Repository."""
        return Mock()

    @pytest.fixture
    def mock_statement_repository(self):
        """Mock Statement Entry Repository."""
        return Mock()

    @pytest.fixture
    def mock_transaction_repository(self):
        """Mock Transaction Repository."""
        return Mock()

    @pytest.fixture
    def use_case(
        self,
        mock_uow,
        mock_account_repository,
        mock_statement_repository,
        mock_transaction_repository,
    ):
        """Create use case instance."""
        mock_uow.statement_repository = mock_statement_repository
        return PostPendingEntriesUseCase(
            uow=mock_uow,
            account_repository=mock_account_repository,
            statement_repository=mock_statement_repository,
            transaction_repository=mock_transaction_repository,
        )

    @pytest.fixture
    def source_account(self):
        """Create source account."""
        return Account.create(
            code="Assets:Bank:Checking",
            name="Checking Account",
            account_type=AccountType.ASSET,
            currency="BRL",
        )

    @pytest.fixture
    def expense_account(self):
        """Create expense account."""
        return Account.create(
            code="Expenses:Groceries",
            name="Groceries",
            account_type=AccountType.EXPENSE,
            currency="BRL",
        )

    def test_no_entries_returns_empty(
        self, use_case, mock_account_repository, mock_statement_repository
    ):
        """When no imported entries exist, return empty result."""
        mock_statement_repository.find_by_status.return_value = []
        mock_account_repository.find_by_code.return_value = Account.create(
            code="Assets:Bank", name="Bank", account_type=AccountType.ASSET, currency="BRL"
        )

        result = use_case.execute(
            PostPendingEntriesCommand(source_account_code="Assets:Bank")
        )

        assert isinstance(result, PostPendingEntriesResult)
        assert result.total_entries == 0
        assert result.posted_count == 0
        assert result.skipped_count == 0
        assert result.error_count == 0

    def test_source_account_not_found_raises_error(
        self, use_case, mock_account_repository
    ):
        """Raises error when source account doesn't exist."""
        mock_account_repository.find_by_code.return_value = None

        with pytest.raises(ValueError, match="Source account not found"):
            use_case.execute(
                PostPendingEntriesCommand(source_account_code="Assets:Invalid")
            )

    def test_post_expense_entry(
        self,
        use_case,
        mock_account_repository,
        mock_statement_repository,
        mock_transaction_repository,
        source_account,
        expense_account,
    ):
        """Successfully posts expense entry."""
        # Create entry with suggested account
        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="001",
            memo="MERCADO EXTRA",
            amount=Decimal("-150.00"),
            currency="BRL",
            occurred_at=datetime(2025, 10, 12),
        )
        entry.suggest_account(expense_account.id)

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value = source_account
        mock_account_repository.get.return_value = expense_account

        # Mock transaction save
        def mock_save(transaction):
            return transaction

        mock_transaction_repository.add.side_effect = mock_save

        # Execute
        result = use_case.execute(
            PostPendingEntriesCommand(
                source_account_code="Assets:Bank:Checking", auto_post=True
            )
        )

        # Assert
        assert result.total_entries == 1
        assert result.posted_count == 1
        assert result.skipped_count == 0
        assert result.error_count == 0
        assert len(result.posted_entries) == 1

        posted = result.posted_entries[0]
        assert posted.entry_id == entry.id
        assert posted.external_id == "001"
        assert posted.amount == Decimal("-150.00")
        assert posted.source_account == "Assets:Bank:Checking"
        assert posted.target_account == "Expenses:Groceries"

        # Verify transaction was saved
        mock_transaction_repository.add.assert_called_once()

    def test_post_income_entry(
        self,
        use_case,
        mock_account_repository,
        mock_statement_repository,
        mock_transaction_repository,
        source_account,
    ):
        """Successfully posts income entry."""
        income_account = Account.create(
            code="Income:Salary",
            name="Salary",
            account_type=AccountType.INCOME,
            currency="BRL",
        )

        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="002",
            memo="SALÁRIO",
            amount=Decimal("5000.00"),  # Positive = income
            currency="BRL",
            occurred_at=datetime(2025, 10, 1),
        )
        entry.suggest_account(income_account.id)

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value = source_account
        mock_account_repository.get.return_value = income_account

        def mock_save(transaction):
            return transaction

        mock_transaction_repository.add.side_effect = mock_save

        result = use_case.execute(
            PostPendingEntriesCommand(source_account_code="Assets:Bank:Checking")
        )

        assert result.posted_count == 1
        posted = result.posted_entries[0]
        assert posted.amount == Decimal("5000.00")
        assert posted.target_account == "Income:Salary"

    def test_post_only_selected_entries(
        self,
        use_case,
        mock_account_repository,
        mock_statement_repository,
        mock_transaction_repository,
        source_account,
        expense_account,
    ):
        """Posts only entries provided in entry_ids."""
        entry_keep = StatementEntry.create(
            batch_id=uuid4(),
            external_id="SEL-001",
            memo="Should post",
            amount=Decimal("-20.00"),
            currency="BRL",
            occurred_at=datetime(2025, 9, 10),
        )
        entry_keep.suggest_account(expense_account.id)

        entry_skip = StatementEntry.create(
            batch_id=uuid4(),
            external_id="SEL-002",
            memo="Should skip",
            amount=Decimal("-30.00"),
            currency="BRL",
            occurred_at=datetime(2025, 9, 11),
        )
        entry_skip.suggest_account(expense_account.id)

        mock_statement_repository.find_by_status.return_value = [
            entry_keep,
            entry_skip,
        ]
        mock_account_repository.find_by_code.return_value = source_account
        mock_account_repository.get.return_value = expense_account
        mock_transaction_repository.add.side_effect = lambda txn: txn

        result = use_case.execute(
            PostPendingEntriesCommand(
                source_account_code="Assets:Bank:Checking",
                auto_post=True,
                entry_ids=(entry_keep.id,),
            )
        )

        assert result.total_entries == 1
        assert result.posted_count == 1
        assert result.posted_entries[0].entry_id == entry_keep.id
        mock_transaction_repository.add.assert_called_once()

    def test_skip_entries_without_suggested_account(
        self,
        use_case,
        mock_account_repository,
        mock_statement_repository,
        source_account,
    ):
        """Skips entries without suggested account when auto_post=True."""
        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="003",
            memo="UNKNOWN STORE",
            amount=Decimal("-50.00"),
            currency="BRL",
            occurred_at=datetime.now(),
        )
        # No suggested account

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value = source_account

        result = use_case.execute(
            PostPendingEntriesCommand(
                source_account_code="Assets:Bank:Checking", auto_post=True
            )
        )

        assert result.total_entries == 1
        assert result.posted_count == 0
        assert result.skipped_count == 1

    def test_dry_run_does_not_save(
        self,
        use_case,
        mock_account_repository,
        mock_statement_repository,
        mock_transaction_repository,
        mock_uow,
        source_account,
        expense_account,
    ):
        """Dry run mode does not save changes."""
        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="004",
            memo="MERCADO",
            amount=Decimal("-100.00"),
            currency="BRL",
            occurred_at=datetime.now(),
        )
        entry.suggest_account(expense_account.id)

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value = source_account
        mock_account_repository.get.return_value = expense_account

        result = use_case.execute(
            PostPendingEntriesCommand(
                source_account_code="Assets:Bank:Checking", dry_run=True
            )
        )

        # Should report as posted but not actually save
        assert result.posted_count == 1
        mock_transaction_repository.add.assert_not_called()
        mock_statement_repository.save.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_filter_by_batch_id(
        self,
        use_case,
        mock_account_repository,
        mock_statement_repository,
        mock_transaction_repository,
        source_account,
        expense_account,
    ):
        """Filters entries by batch_id when provided."""
        batch_id = uuid4()
        entry = StatementEntry.create(
            batch_id=batch_id,
            external_id="005",
            memo="MERCADO",
            amount=Decimal("-100.00"),
            currency="BRL",
            occurred_at=datetime.now(),
        )
        entry.suggest_account(expense_account.id)

        mock_statement_repository.find_by_batch_id.return_value = [entry]
        mock_account_repository.find_by_code.return_value = source_account
        mock_account_repository.get.return_value = expense_account

        def mock_save(transaction):
            return transaction

        mock_transaction_repository.add.side_effect = mock_save

        result = use_case.execute(
            PostPendingEntriesCommand(
                batch_id=batch_id, source_account_code="Assets:Bank:Checking"
            )
        )

        assert result.posted_count == 1
        mock_statement_repository.find_by_batch_id.assert_called_once_with(batch_id)

    def test_handles_errors_gracefully(
        self,
        use_case,
        mock_account_repository,
        mock_statement_repository,
        mock_transaction_repository,
        source_account,
        expense_account,
    ):
        """Handles errors during posting gracefully."""
        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="006",
            memo="MERCADO",
            amount=Decimal("-100.00"),
            currency="BRL",
            occurred_at=datetime.now(),
        )
        entry.suggest_account(expense_account.id)

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value = source_account
        mock_account_repository.get.side_effect = Exception("Database error")

        result = use_case.execute(
            PostPendingEntriesCommand(source_account_code="Assets:Bank:Checking")
        )

        assert result.total_entries == 1
        assert result.posted_count == 0
        assert result.error_count == 1
        assert len(result.errors) == 1
        assert result.errors[0][0] == entry.id
        assert "Database error" in result.errors[0][1]

    def test_transaction_balance(
        self,
        use_case,
        mock_account_repository,
        mock_statement_repository,
        mock_transaction_repository,
        source_account,
        expense_account,
    ):
        """Verifies created transaction is balanced."""
        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="007",
            memo="MERCADO",
            amount=Decimal("-100.00"),
            currency="BRL",
            occurred_at=datetime.now(),
        )
        entry.suggest_account(expense_account.id)

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value = source_account
        mock_account_repository.get.return_value = expense_account

        saved_transaction = None

        def capture_transaction(transaction):
            nonlocal saved_transaction
            saved_transaction = transaction
            return transaction

        mock_transaction_repository.add.side_effect = capture_transaction

        use_case.execute(
            PostPendingEntriesCommand(source_account_code="Assets:Bank:Checking")
        )

        # Verify transaction was created and is balanced
        assert saved_transaction is not None
        assert len(saved_transaction.postings) == 2
        total = sum(p.amount.amount for p in saved_transaction.postings)
        assert total == Decimal("0")  # Balanced
