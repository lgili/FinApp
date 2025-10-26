"""Tests for MonthlyTaxReportUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from finlite.application.use_cases.generate_monthly_tax_report import (
    GenerateMonthlyTaxReportCommand,
    MonthlyTaxReportUseCase,
)
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting


def make_transaction(
    year: int,
    month: int,
    day: int,
    tags: tuple[str, ...],
) -> Transaction:
    """Helper to create balanced transaction with tax tags."""
    account_a = uuid4()
    account_b = uuid4()
    postings = [
        Posting(account_a, Money.from_float(100.0, "BRL")),
        Posting(account_b, Money.from_float(-100.0, "BRL")),
    ]
    return Transaction.create(
        date=date(year, month, day),
        description="Test",
        postings=postings,
        tags=list(tags),
    )


@pytest.fixture
def mock_uow():
    """Create mocked unit of work with transaction repository."""
    uow = Mock()
    uow.__enter__ = Mock(return_value=uow)
    uow.__exit__ = Mock(return_value=False)
    uow.transactions = Mock()
    return uow


class TestMonthlyTaxReportUseCase:
    """Unit tests for monthly tax calculations."""

    def test_no_transactions_returns_zero_report(self, mock_uow):
        mock_uow.transactions.find_by_date_range.return_value = []
        use_case = MonthlyTaxReportUseCase(uow=mock_uow)

        result = use_case.execute(
            GenerateMonthlyTaxReportCommand(month=date(2025, 10, 1), currency="BRL")
        )

        breakdown = result.breakdown
        assert breakdown.total_sales == Decimal("0")
        assert breakdown.taxable_base == Decimal("0")
        assert breakdown.darf_tax_payable == Decimal("0")
        assert breakdown.loss_carry_out == Decimal("0")

    def test_exempt_sales_month(self, mock_uow):
        txn = make_transaction(
            2025,
            10,
            15,
            tags=(
                "tax:sale=15000",
                "tax:gain=1200",
                "tax:currency=BRL",
            ),
        )
        mock_uow.transactions.find_by_date_range.return_value = [txn]

        use_case = MonthlyTaxReportUseCase(uow=mock_uow)
        result = use_case.execute(
            GenerateMonthlyTaxReportCommand(month=date(2025, 10, 1), currency="BRL")
        )

        breakdown = result.breakdown
        assert breakdown.total_sales == Decimal("15000")
        assert breakdown.exempt_sales == Decimal("15000")
        assert breakdown.taxable_base == Decimal("0")
        assert breakdown.loss_carry_out == Decimal("0")

    def test_carryover_applied_to_taxable_gain(self, mock_uow):
        september_loss = make_transaction(
            2025,
            9,
            20,
            tags=(
                "tax:sale=30000",
                "tax:loss=2000",
                "tax:currency=BRL",
            ),
        )
        october_gain = make_transaction(
            2025,
            10,
            25,
            tags=(
                "tax:sale=40000",
                "tax:gain=5000",
                "tax:withheld=100",
                "tax:dividend=250",
                "tax:jcp=120",
                "tax:currency=BRL",
            ),
        )
        mock_uow.transactions.find_by_date_range.return_value = [
            september_loss,
            october_gain,
        ]

        use_case = MonthlyTaxReportUseCase(uow=mock_uow)
        result = use_case.execute(
            GenerateMonthlyTaxReportCommand(month=date(2025, 10, 1), currency="BRL")
        )

        breakdown = result.breakdown
        assert breakdown.loss_carry_in == Decimal("2000")
        assert breakdown.loss_carry_applied == Decimal("2000")
        assert breakdown.taxable_base == Decimal("3000")
        assert breakdown.darf_tax_due == Decimal("450.00")
        assert breakdown.darf_tax_payable == Decimal("350.00")
        assert breakdown.dividends == Decimal("250")
        assert breakdown.jcp == Decimal("120")
