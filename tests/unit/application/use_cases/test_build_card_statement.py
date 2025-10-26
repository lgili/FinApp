"""Tests for BuildCardStatementUseCase."""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from finlite.application.use_cases.build_card_statement import (
    BuildCardStatementCommand,
    BuildCardStatementUseCase,
)
from finlite.domain.entities import Account
from finlite.domain.entities.card_statement import CardStatementRecord
from finlite.domain.value_objects import AccountType
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting


def make_account(code: str, issuer: str | None = None) -> Account:
    return Account.create(
        code=code,
        name=code.split(":")[-1],
        account_type=AccountType.LIABILITY,
        currency="BRL",
        card_issuer=issuer,
        card_closing_day=7,
        card_due_day=15,
    )


def make_transaction(amount: Decimal, account_id, tags=()) -> Transaction:
    other = uuid4()
    postings = [
        Posting(account_id, Money(amount=-amount, currency="BRL")),
        Posting(other, Money(amount=amount, currency="BRL")),
    ]
    return Transaction.create(
        date=date(2025, 10, 5),
        description="Purchase",
        postings=postings,
        tags=list(tags),
    )


class TestBuildCardStatementUseCase:
    @pytest.fixture
    def repositories(self):
        account_repo = Mock()
        transaction_repo = Mock()
        statement_repo = Mock()
        return account_repo, transaction_repo, statement_repo

    @pytest.fixture
    def use_case(self, repositories):
        uow = Mock()
        uow.__enter__ = Mock(return_value=uow)
        uow.__exit__ = Mock(return_value=False)
        account_repo, transaction_repo, statement_repo = repositories
        return BuildCardStatementUseCase(
            uow=uow,
            account_repository=account_repo,
            transaction_repository=transaction_repo,
            card_statement_repository=statement_repo,
        )

    def test_builds_statement_from_transactions(self, use_case, repositories):
        account_repo, transaction_repo, statement_repo = repositories
        card_account = make_account("Liabilities:CreditCard:Nubank", issuer="Nubank")
        expense_account = Account.create(
            code="Expenses:Food",
            name="Food",
            account_type=AccountType.EXPENSE,
            currency="BRL",
        )
        transaction = make_transaction(Decimal("150.00"), card_account.id, tags=("card:installment=1/3",))
        account_repo.find_by_code.return_value = card_account
        account_repo.list_all.return_value = [card_account, expense_account]
        transaction_repo.find_by_date_range.side_effect = [
            [transaction],  # current period
            [],  # previous balance
        ]
        statement_repo.find_by_period.return_value = None

        statement_repo.save.side_effect = lambda record: record

        result = use_case.execute(
            BuildCardStatementCommand(
                card_account_code="Liabilities:CreditCard:Nubank",
                period=date(2025, 10, 1),
                currency="BRL",
            )
        )

        assert result.card_account_code == "Liabilities:CreditCard:Nubank"
        assert result.period_end == date(2025, 10, 7)
        assert result.due_date == date(2025, 10, 15)
        assert result.charges_total == Decimal("150.00")

        saved_record: CardStatementRecord = statement_repo.save.call_args[0][0]
        assert saved_record.total_amount == Decimal("150.00")
        assert len(saved_record.items) == 1
        item = saved_record.items[0]
        assert item.installment_number == 1
        assert item.installment_total == 3

    def test_requires_card_metadata(self, use_case, repositories):
        account_repo, transaction_repo, statement_repo = repositories
        card_account = Account.create(
            code="Liabilities:CreditCard:Nubank",
            name="Card",
            account_type=AccountType.LIABILITY,
            currency="BRL",
        )
        account_repo.find_by_code.return_value = card_account

        with pytest.raises(ValueError):
            use_case.execute(
                BuildCardStatementCommand(
                    card_account_code="Liabilities:CreditCard:Nubank",
                    period=date(2025, 10, 1),
                    currency="BRL",
                )
            )
