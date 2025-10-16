"""Tests for ApplyRulesUseCase."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from finlite.application.use_cases.apply_rules import (
    ApplyRulesCommand,
    ApplyRulesResult,
    ApplyRulesUseCase,
)
from finlite.config import Settings
from finlite.domain.entities.account import Account
from finlite.domain.entities.statement_entry import StatementEntry
from finlite.domain.value_objects.account_type import AccountType
from finlite.rules.mapping import MapRule


class TestApplyRulesUseCase:
    """Tests for ApplyRulesUseCase."""

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
    def mock_settings(self):
        """Mock Settings."""
        return Mock(spec=Settings)

    @pytest.fixture
    def use_case(
        self, mock_uow, mock_account_repository, mock_statement_repository, mock_settings
    ):
        """Create use case instance."""
        return ApplyRulesUseCase(
            uow=mock_uow,
            account_repository=mock_account_repository,
            statement_repository=mock_statement_repository,
            settings=mock_settings,
        )

    def test_no_rules_returns_empty_result(
        self, use_case, mock_statement_repository
    ):
        """When no rules exist, return empty result."""
        with patch("finlite.application.use_cases.apply_rules.load_rules", return_value=[]):
            result = use_case.execute(ApplyRulesCommand())

            assert isinstance(result, ApplyRulesResult)
            assert result.total_entries == 0
            assert result.matched_entries == 0

    def test_no_imported_entries_returns_empty(
        self, use_case, mock_statement_repository
    ):
        """When no imported entries exist, return empty result."""
        mock_statement_repository.find_by_status.return_value = []

        rules = [
            MapRule(pattern="mercado", account="Expenses:Groceries", type="expense")
        ]

        with patch("finlite.application.use_cases.apply_rules.load_rules", return_value=rules):
            result = use_case.execute(ApplyRulesCommand())

            assert result.total_entries == 0
            assert result.matched_entries == 0

    def test_matches_expense_rule(
        self, use_case, mock_account_repository, mock_statement_repository
    ):
        """Successfully matches expense rule."""
        # Setup
        batch_id = uuid4()
        entry = StatementEntry.create(
            batch_id=batch_id,
            external_id="001",
            memo="MERCADO EXTRA",
            amount=Decimal("-150.00"),
            currency="BRL",
            occurred_at=datetime(2025, 10, 12),
        )

        expense_account = Account.create(
            code="Expenses:Groceries",
            name="Groceries",
            account_type=AccountType.EXPENSE,
            currency="BRL",
        )

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value = expense_account

        rules = [
            MapRule(pattern="mercado", account="Expenses:Groceries", type="expense")
        ]

        # Execute
        with patch("finlite.application.use_cases.apply_rules.load_rules", return_value=rules):
            result = use_case.execute(ApplyRulesCommand(auto_apply=True))

        # Assert
        assert result.total_entries == 1
        assert result.matched_entries == 1
        assert len(result.applications) == 1

        app = result.applications[0]
        assert app.entry_id == entry.id
        assert app.suggested_account_code == "Expenses:Groceries"
        assert app.confidence == "high"

    def test_matches_income_rule(
        self, use_case, mock_account_repository, mock_statement_repository
    ):
        """Successfully matches income rule."""
        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="002",
            memo="SALÁRIO",
            amount=Decimal("5000.00"),  # Positive = income
            currency="BRL",
            occurred_at=datetime(2025, 10, 1),
        )

        income_account = Account.create(
            code="Income:Salary",
            name="Salary",
            account_type=AccountType.INCOME,
            currency="BRL",
        )

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value=income_account

        rules = [
            MapRule(pattern="salário", account="Income:Salary", type="income")
        ]

        with patch("finlite.application.use_cases.apply_rules.load_rules", return_value=rules):
            result = use_case.execute(ApplyRulesCommand())

        assert result.matched_entries == 1
        assert result.applications[0].suggested_account_code == "Income:Salary"

    def test_dry_run_does_not_save(
        self, use_case, mock_account_repository, mock_statement_repository, mock_uow
    ):
        """Dry run mode does not save changes."""
        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="003",
            memo="MERCADO",
            amount=Decimal("-100.00"),
            currency="BRL",
            occurred_at=datetime.now(),
        )

        account = Account.create(
            code="Expenses:Groceries",
            name="Groceries",
            account_type=AccountType.EXPENSE,
            currency="BRL",
        )

        mock_statement_repository.find_by_status.return_value = [entry]
        mock_account_repository.find_by_code.return_value = account

        rules = [MapRule(pattern="mercado", account="Expenses:Groceries", type="expense")]

        with patch("finlite.application.use_cases.apply_rules.load_rules", return_value=rules):
            result = use_case.execute(ApplyRulesCommand(dry_run=True))

        # Verify no commit was called
        mock_uow.commit.assert_not_called()
        assert result.matched_entries == 1

    def test_no_match_returns_unmatched(
        self, use_case, mock_account_repository, mock_statement_repository
    ):
        """Entry with no matching rule is marked as unmatched."""
        entry = StatementEntry.create(
            batch_id=uuid4(),
            external_id="004",
            memo="UNKNOWN STORE",
            amount=Decimal("-50.00"),
            currency="BRL",
            occurred_at=datetime.now(),
        )

        mock_statement_repository.find_by_status.return_value = [entry]

        rules = [
            MapRule(pattern="mercado", account="Expenses:Groceries", type="expense")
        ]

        with patch("finlite.application.use_cases.apply_rules.load_rules", return_value=rules):
            result = use_case.execute(ApplyRulesCommand())

        assert result.total_entries == 1
        assert result.matched_entries == 0
        assert result.unmatched_entries == 1
        assert result.applications[0].suggested_account_code is None
        assert result.applications[0].confidence == "none"
