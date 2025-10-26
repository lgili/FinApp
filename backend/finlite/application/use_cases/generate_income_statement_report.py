"""
Generate Income Statement Report Use Case.

Produces a profit and loss statement showing revenues and expenses over a period.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, Iterable, Optional
from uuid import UUID

from finlite.domain.entities.account import Account
from finlite.domain.entities.transaction import Transaction
from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.transaction_repository import ITransactionRepository
from finlite.domain.value_objects.account_type import AccountType
from finlite.infrastructure.persistence.unit_of_work import UnitOfWork


class ComparisonMode(str, Enum):
    """Comparison modes for income statement."""

    NONE = "NONE"
    PREVIOUS_PERIOD = "PREVIOUS_PERIOD"
    YEAR_OVER_YEAR = "YEAR_OVER_YEAR"


@dataclass(frozen=True)
class GenerateIncomeStatementCommand:
    """Command parameters for income statement generation."""

    from_date: date
    to_date: date
    currency: str = "USD"
    comparison_mode: ComparisonMode = ComparisonMode.NONE


@dataclass(frozen=True)
class IncomeStatementAccountRow:
    """Detailed income statement line for an individual account."""

    account_code: str
    account_name: str
    account_type: AccountType
    amount: Decimal  # Normalized amount (positive for income, expenses shown as positive)
    raw_amount: Decimal  # Sum of postings without normalization
    transaction_count: int
    comparison_amount: Optional[Decimal] = None  # Amount from comparison period
    change_amount: Optional[Decimal] = None  # Difference from comparison period
    change_percent: Optional[Decimal] = None  # Percentage change from comparison period


@dataclass(frozen=True)
class IncomeStatementReport:
    """Income statement with revenues, expenses, and net income."""

    from_date: date
    to_date: date
    currency: str
    revenue: list[IncomeStatementAccountRow]
    expenses: list[IncomeStatementAccountRow]
    revenue_total: Decimal
    expenses_total: Decimal
    net_income: Decimal
    comparison_mode: ComparisonMode
    comparison_from_date: Optional[date] = None
    comparison_to_date: Optional[date] = None
    comparison_revenue_total: Optional[Decimal] = None
    comparison_expenses_total: Optional[Decimal] = None
    comparison_net_income: Optional[Decimal] = None


class GenerateIncomeStatementReportUseCase:
    """Use case that aggregates revenues and expenses for an income statement."""

    def __init__(
        self,
        uow: UnitOfWork,
        account_repository: IAccountRepository,
        transaction_repository: ITransactionRepository,
    ) -> None:
        self._uow = uow
        self._account_repository = account_repository
        self._transaction_repository = transaction_repository

    def execute(self, command: GenerateIncomeStatementCommand) -> IncomeStatementReport:
        """
        Generate income statement for the provided period.

        Args:
            command: Parameters describing the period and comparison mode.

        Returns:
            IncomeStatementReport with per-account rows and aggregated totals.
        """
        currency = command.currency.upper()
        from_date = self._normalize_date(command.from_date)
        to_date = self._normalize_date(command.to_date)

        with self._uow:
            accounts = self._account_repository.list_all()
            income_accounts = self._filter_income_statement_accounts(accounts, currency)

            if not income_accounts:
                zero = Decimal("0")
                return IncomeStatementReport(
                    from_date=from_date,
                    to_date=to_date,
                    currency=currency,
                    revenue=[],
                    expenses=[],
                    revenue_total=zero,
                    expenses_total=zero,
                    net_income=zero,
                    comparison_mode=command.comparison_mode,
                )

            # Get transactions for current period
            transactions = self._transaction_repository.find_by_date_range(
                start_date=from_date,
                end_date=to_date,
            )

            balances, counts = self._aggregate_postings(
                transactions=transactions,
                accounts=income_accounts,
                currency=currency,
            )

            # Handle comparison if requested
            comparison_balances = None
            comparison_from = None
            comparison_to = None

            if command.comparison_mode != ComparisonMode.NONE:
                comparison_from, comparison_to = self._calculate_comparison_dates(
                    from_date, to_date, command.comparison_mode
                )
                comparison_txns = self._transaction_repository.find_by_date_range(
                    start_date=comparison_from,
                    end_date=comparison_to,
                )
                comparison_balances, _ = self._aggregate_postings(
                    transactions=comparison_txns,
                    accounts=income_accounts,
                    currency=currency,
                )

            sections = self._build_sections(
                income_accounts, balances, counts, comparison_balances
            )

            revenue_total = self._sum_amounts(sections[AccountType.INCOME])
            expenses_total = self._sum_amounts(sections[AccountType.EXPENSE])
            net_income = revenue_total - expenses_total

            # Calculate comparison totals if applicable
            comparison_revenue_total = None
            comparison_expenses_total = None
            comparison_net_income = None

            if comparison_balances is not None:
                comparison_revenue_total = sum(
                    (row.comparison_amount or Decimal("0"))
                    for row in sections[AccountType.INCOME]
                )
                comparison_expenses_total = sum(
                    (row.comparison_amount or Decimal("0"))
                    for row in sections[AccountType.EXPENSE]
                )
                comparison_net_income = (
                    comparison_revenue_total - comparison_expenses_total
                )

            return IncomeStatementReport(
                from_date=from_date,
                to_date=to_date,
                currency=currency,
                revenue=sections[AccountType.INCOME],
                expenses=sections[AccountType.EXPENSE],
                revenue_total=revenue_total,
                expenses_total=expenses_total,
                net_income=net_income,
                comparison_mode=command.comparison_mode,
                comparison_from_date=comparison_from,
                comparison_to_date=comparison_to,
                comparison_revenue_total=comparison_revenue_total,
                comparison_expenses_total=comparison_expenses_total,
                comparison_net_income=comparison_net_income,
            )

    @staticmethod
    def _normalize_date(dt: date | datetime) -> date:
        """Ensure we work with a pure date value."""
        if isinstance(dt, datetime):
            return dt.date()
        return dt

    @staticmethod
    def _filter_income_statement_accounts(
        accounts: Iterable[Account],
        currency: str,
    ) -> Dict[UUID, Account]:
        """Keep only income statement accounts for the requested currency."""
        result: Dict[UUID, Account] = {}
        for account in accounts:
            if not account.account_type.is_income_statement_account():
                continue
            if account.currency.upper() != currency:
                continue
            result[account.id] = account
        return result

    @staticmethod
    def _aggregate_postings(
        transactions: Iterable[Transaction],
        accounts: Dict[UUID, Account],
        currency: str,
    ) -> tuple[Dict[UUID, Decimal], Dict[UUID, int]]:
        """Aggregate postings into amounts/counts per account."""
        balances: Dict[UUID, Decimal] = {
            account_id: Decimal("0") for account_id in accounts
        }
        counts: Dict[UUID, int] = {account_id: 0 for account_id in accounts}

        for transaction in transactions:
            for posting in transaction.postings:
                if posting.amount.currency.upper() != currency:
                    continue
                account = accounts.get(posting.account_id)
                if not account:
                    continue
                balances[posting.account_id] += posting.amount.amount
                counts[posting.account_id] += 1

        return balances, counts

    @staticmethod
    def _calculate_comparison_dates(
        from_date: date, to_date: date, mode: ComparisonMode
    ) -> tuple[date, date]:
        """Calculate the comparison period dates."""
        period_length = (to_date - from_date).days + 1

        if mode == ComparisonMode.PREVIOUS_PERIOD:
            # Previous period of same length
            comparison_to = from_date - timedelta(days=1)
            comparison_from = comparison_to - timedelta(days=period_length - 1)
        elif mode == ComparisonMode.YEAR_OVER_YEAR:
            # Same period last year
            try:
                comparison_from = from_date.replace(year=from_date.year - 1)
                comparison_to = to_date.replace(year=to_date.year - 1)
            except ValueError:
                # Handle leap year edge case (Feb 29)
                comparison_from = from_date.replace(
                    year=from_date.year - 1, day=28
                )
                comparison_to = to_date.replace(year=to_date.year - 1, day=28)
        else:
            raise ValueError(f"Unsupported comparison mode: {mode}")

        return comparison_from, comparison_to

    @staticmethod
    def _build_sections(
        accounts: Dict[UUID, Account],
        balances: Dict[UUID, Decimal],
        counts: Dict[UUID, int],
        comparison_balances: Optional[Dict[UUID, Decimal]] = None,
    ) -> Dict[AccountType, list[IncomeStatementAccountRow]]:
        """Build per-account rows grouped by account type."""
        sections: Dict[AccountType, list[IncomeStatementAccountRow]] = {
            AccountType.INCOME: [],
            AccountType.EXPENSE: [],
        }

        for account_id, account in accounts.items():
            balance = balances.get(account_id, Decimal("0"))
            count = counts.get(account_id, 0)

            # Skip accounts with no activity
            if balance == Decimal("0") and count == 0:
                continue

            # Normalize: INCOME credits are positive revenue, EXPENSE debits are positive expenses
            # For INCOME: negative raw balance (credits) -> positive amount
            # For EXPENSE: positive raw balance (debits) -> positive amount
            if account.account_type == AccountType.INCOME:
                normalized = abs(balance)  # Income credits shown as positive
            else:  # EXPENSE
                normalized = abs(balance)  # Expense debits shown as positive

            # Handle comparison data
            comparison_amount = None
            change_amount = None
            change_percent = None

            if comparison_balances is not None:
                comp_balance = comparison_balances.get(account_id, Decimal("0"))
                if account.account_type == AccountType.INCOME:
                    comparison_amount = abs(comp_balance)
                else:  # EXPENSE
                    comparison_amount = abs(comp_balance)

                change_amount = normalized - comparison_amount
                if comparison_amount != Decimal("0"):
                    change_percent = (change_amount / comparison_amount) * Decimal("100")

            sections[account.account_type].append(
                IncomeStatementAccountRow(
                    account_code=account.code,
                    account_name=account.name,
                    account_type=account.account_type,
                    amount=normalized,
                    raw_amount=balance,
                    transaction_count=count,
                    comparison_amount=comparison_amount,
                    change_amount=change_amount,
                    change_percent=change_percent,
                )
            )

        # Sort by amount descending
        for rows in sections.values():
            rows.sort(key=lambda item: (item.amount, item.account_code), reverse=True)

        return sections

    @staticmethod
    def _sum_amounts(rows: Iterable[IncomeStatementAccountRow]) -> Decimal:
        """Sum normalized amounts for a section."""
        total = Decimal("0")
        for row in rows:
            total += row.amount
        return total
