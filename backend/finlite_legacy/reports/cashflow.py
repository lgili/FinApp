"""Cashflow reporting utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finlite.db.models import Account, AccountType, Posting, Transaction

_CASH_QUANT = Decimal("0.01")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_CASH_QUANT, rounding=ROUND_HALF_UP)


@dataclass(slots=True)
class CashflowRow:
    account_id: int
    account_name: str
    amount: Decimal


@dataclass(slots=True)
class CashflowSection:
    rows: list[CashflowRow] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        raw_total = sum((row.amount for row in self.rows), Decimal("0"))
        return _quantize(raw_total)


@dataclass(slots=True)
class CashflowReport:
    start: datetime
    end: datetime
    currency: str
    income: CashflowSection
    expenses: CashflowSection

    @property
    def net(self) -> Decimal:
        return _quantize(self.income.total - self.expenses.total)


def _normalise_amount(account_type: AccountType, total: Decimal | None) -> Decimal | None:
    if total is None:
        return None
    if account_type == AccountType.INCOME:
        normalised = -total
    elif account_type == AccountType.EXPENSE:
        normalised = total
    else:
        return None
    return _quantize(normalised)


def generate_cashflow(
    session: Session, start: datetime, end: datetime, currency: str
) -> CashflowReport:
    """Create a cashflow report for the interval [start, end)."""
    stmt = (
        select(
            Account.id,
            Account.name,
            Account.type,
            func.sum(Posting.amount).label("total"),
        )
        .select_from(Posting)
        .join(Account, Posting.account_id == Account.id)
        .join(Transaction, Posting.transaction_id == Transaction.id)
        .where(
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
            Posting.currency == currency,
        )
        .group_by(Account.id, Account.name, Account.type)
    )

    income_rows: list[CashflowRow] = []
    expense_rows: list[CashflowRow] = []

    for account_id, account_name, account_type, total in session.execute(stmt):
        normalised = _normalise_amount(account_type, total)
        if normalised is None:
            continue
        row = CashflowRow(account_id=account_id, account_name=account_name, amount=normalised)
        if account_type == AccountType.INCOME:
            income_rows.append(row)
        else:
            expense_rows.append(row)

    income_rows.sort(key=lambda row: row.amount, reverse=True)
    expense_rows.sort(key=lambda row: row.amount, reverse=True)

    return CashflowReport(
        start=start,
        end=end,
        currency=currency,
        income=CashflowSection(rows=income_rows),
        expenses=CashflowSection(rows=expense_rows),
    )
