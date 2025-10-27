"""
Generate Balance Sheet Report Use Case.

Produces a snapshot of Assets, Liabilities, and Equity as of a target date.
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

EARLIEST_SUPPORTED_DATE = date(1900, 1, 1)


class ComparisonMode(str, Enum):
    """Comparison modes for balance sheet analysis."""

    NONE = "NONE"
    PREVIOUS_MONTH = "PREVIOUS_MONTH"
    CUSTOM_DATE = "CUSTOM_DATE"


@dataclass(frozen=True)
class GenerateBalanceSheetCommand:
    """Command parameters for balance sheet generation."""

    as_of: date
    currency: str = "USD"
    comparison_mode: ComparisonMode = ComparisonMode.NONE
    comparison_date: Optional[date] = None


@dataclass(frozen=True)
class BalanceSheetAccountRow:
    """Detailed balance sheet line for an individual account."""

    account_code: str
    account_name: str
    account_type: AccountType
    balance: Decimal  # Normalized balance (debit-positive for assets, credit-positive for liabilities/equity)
    raw_balance: Decimal  # Sum of postings without normalization
    transaction_count: int
    comparison_balance: Optional[Decimal] = None  # Balance at comparison date
    change_amount: Optional[Decimal] = None  # Absolute change
    change_percent: Optional[Decimal] = None  # Percentage change


@dataclass(frozen=True)
class BalanceSheetReport:
    """Balance sheet snapshot with totals and per-account rows."""

    as_of: date
    currency: str
    assets: list[BalanceSheetAccountRow]
    liabilities: list[BalanceSheetAccountRow]
    equity: list[BalanceSheetAccountRow]
    assets_total: Decimal
    liabilities_total: Decimal
    equity_total: Decimal
    net_worth: Decimal
    comparison_mode: ComparisonMode = ComparisonMode.NONE
    comparison_date: Optional[date] = None
    comparison_assets_total: Optional[Decimal] = None
    comparison_liabilities_total: Optional[Decimal] = None
    comparison_equity_total: Optional[Decimal] = None
    comparison_net_worth: Optional[Decimal] = None


class GenerateBalanceSheetReportUseCase:
    """Use case that aggregates balances by account type for a balance sheet snapshot."""

    def __init__(
        self,
        uow: UnitOfWork,
        account_repository: IAccountRepository,
        transaction_repository: ITransactionRepository,
    ) -> None:
        self._uow = uow
        self._account_repository = account_repository
        self._transaction_repository = transaction_repository

    def execute(self, command: GenerateBalanceSheetCommand) -> BalanceSheetReport:
        """
        Generate balance sheet as of the provided date.

        Args:
            command: Parameters describing the snapshot (date/currency/comparison).

        Returns:
            BalanceSheetReport with per-account rows and aggregated totals.
        """
        currency = command.currency.upper()
        as_of_date = self._normalize_as_of(command.as_of)

        with self._uow:
            accounts = self._account_repository.list_all()
            balance_accounts = self._filter_balance_sheet_accounts(accounts, currency)

            if not balance_accounts:
                zero = Decimal("0")
                return BalanceSheetReport(
                    as_of=as_of_date,
                    currency=currency,
                    assets=[],
                    liabilities=[],
                    equity=[],
                    assets_total=zero,
                    liabilities_total=zero,
                    equity_total=zero,
                    net_worth=zero,
                    comparison_mode=command.comparison_mode,
                    comparison_date=command.comparison_date,
                )

            transactions = self._transaction_repository.find_by_date_range(
                start_date=EARLIEST_SUPPORTED_DATE,
                end_date=as_of_date,
            )

            balances, counts = self._aggregate_postings(
                transactions=transactions,
                accounts=balance_accounts,
                currency=currency,
                as_of=as_of_date,
            )

            # Calculate comparison balances if requested
            comparison_balances: Optional[Dict[UUID, Decimal]] = None
            comparison_date: Optional[date] = None

            if command.comparison_mode != ComparisonMode.NONE:
                comparison_date = self._calculate_comparison_date(
                    as_of_date, command.comparison_mode, command.comparison_date
                )
                comparison_transactions = self._transaction_repository.find_by_date_range(
                    start_date=EARLIEST_SUPPORTED_DATE,
                    end_date=comparison_date,
                )
                comparison_balances, _ = self._aggregate_postings(
                    transactions=comparison_transactions,
                    accounts=balance_accounts,
                    currency=currency,
                    as_of=comparison_date,
                )

            sections = self._build_sections(
                balance_accounts, balances, counts, comparison_balances
            )
            assets_total = self._sum_balances(sections[AccountType.ASSET])
            liabilities_total = self._sum_balances(sections[AccountType.LIABILITY])

            equity_rows = sections[AccountType.EQUITY]
            calculated_equity_total = self._sum_balances(equity_rows)
            if not equity_rows:
                calculated_equity_total = assets_total - liabilities_total

            net_worth = assets_total - liabilities_total

            # Calculate comparison totals if applicable
            comparison_assets_total: Optional[Decimal] = None
            comparison_liabilities_total: Optional[Decimal] = None
            comparison_equity_total: Optional[Decimal] = None
            comparison_net_worth: Optional[Decimal] = None

            if comparison_balances is not None:
                comparison_assets_total = sum(
                    (row.comparison_balance or Decimal("0"))
                    for row in sections[AccountType.ASSET]
                )
                comparison_liabilities_total = sum(
                    (row.comparison_balance or Decimal("0"))
                    for row in sections[AccountType.LIABILITY]
                )
                comparison_equity_total = sum(
                    (row.comparison_balance or Decimal("0"))
                    for row in sections[AccountType.EQUITY]
                )
                if not equity_rows:
                    comparison_equity_total = comparison_assets_total - comparison_liabilities_total
                comparison_net_worth = comparison_assets_total - comparison_liabilities_total

            return BalanceSheetReport(
                as_of=as_of_date,
                currency=currency,
                assets=sections[AccountType.ASSET],
                liabilities=sections[AccountType.LIABILITY],
                equity=equity_rows,
                assets_total=assets_total,
                liabilities_total=liabilities_total,
                equity_total=calculated_equity_total,
                net_worth=net_worth,
                comparison_mode=command.comparison_mode,
                comparison_date=comparison_date,
                comparison_assets_total=comparison_assets_total,
                comparison_liabilities_total=comparison_liabilities_total,
                comparison_equity_total=comparison_equity_total,
                comparison_net_worth=comparison_net_worth,
            )

    @staticmethod
    def _normalize_as_of(as_of: date | datetime) -> date:
        """Ensure we work with a pure date value."""
        if isinstance(as_of, datetime):
            return as_of.date()
        return as_of

    @staticmethod
    def _calculate_comparison_date(
        as_of: date, mode: ComparisonMode, custom_date: Optional[date]
    ) -> date:
        """Calculate comparison date based on mode."""
        if mode == ComparisonMode.CUSTOM_DATE:
            if custom_date is None:
                raise ValueError("Custom comparison date required for CUSTOM_DATE mode")
            return custom_date
        elif mode == ComparisonMode.PREVIOUS_MONTH:
            # Go back one month (approximate)
            if as_of.month == 1:
                return date(as_of.year - 1, 12, as_of.day)
            else:
                # Handle month-end edge cases
                try:
                    return date(as_of.year, as_of.month - 1, as_of.day)
                except ValueError:
                    # Day doesn't exist in previous month (e.g., Jan 31 -> Feb 28)
                    # Use last day of previous month
                    prev_month = as_of.month - 1
                    if prev_month == 0:
                        prev_month = 12
                        year = as_of.year - 1
                    else:
                        year = as_of.year
                    # Get last day of previous month
                    next_month_first = date(year, prev_month, 1) + timedelta(days=32)
                    last_day = (next_month_first.replace(day=1) - timedelta(days=1)).day
                    return date(year, prev_month, min(as_of.day, last_day))
        return as_of

    @staticmethod
    def _filter_balance_sheet_accounts(
        accounts: Iterable[Account],
        currency: str,
    ) -> Dict[UUID, Account]:
        """Keep only balance sheet accounts for the requested currency."""
        result: Dict[UUID, any] = {}
        for account in accounts:
            if not account.account_type.is_balance_sheet_account():
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
        as_of: date,
    ) -> tuple[Dict[UUID, Decimal], Dict[UUID, int]]:
        """Aggregate postings into balances/counts per account."""
        balances: Dict[UUID, Decimal] = {account_id: Decimal("0") for account_id in accounts}
        counts: Dict[UUID, int] = {account_id: 0 for account_id in accounts}

        for transaction in transactions:
            if transaction.date > as_of:
                continue
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
    def _build_sections(
        accounts: Dict[UUID, Account],
        balances: Dict[UUID, Decimal],
        counts: Dict[UUID, int],
        comparison_balances: Optional[Dict[UUID, Decimal]] = None,
    ) -> Dict[AccountType, list[BalanceSheetAccountRow]]:
        """Build per-account rows grouped by account type."""
        sections: Dict[AccountType, list[BalanceSheetAccountRow]] = {
            AccountType.ASSET: [],
            AccountType.LIABILITY: [],
            AccountType.EQUITY: [],
        }

        for account_id, account in accounts.items():
            balance = balances.get(account_id, Decimal("0"))
            count = counts.get(account_id, 0)

            # Skip accounts with no activity in either period
            comparison_balance_raw = (
                comparison_balances.get(account_id, Decimal("0"))
                if comparison_balances is not None
                else None
            )
            if balance == Decimal("0") and count == 0:
                if comparison_balance_raw is None or comparison_balance_raw == Decimal("0"):
                    continue

            normalized = balance * Decimal(account.account_type.get_sign_multiplier())

            # Calculate comparison fields
            comparison_balance_normalized: Optional[Decimal] = None
            change_amount: Optional[Decimal] = None
            change_percent: Optional[Decimal] = None

            if comparison_balance_raw is not None:
                comparison_balance_normalized = comparison_balance_raw * Decimal(
                    account.account_type.get_sign_multiplier()
                )
                change_amount = normalized - comparison_balance_normalized
                if comparison_balance_normalized != Decimal("0"):
                    change_percent = (change_amount / abs(comparison_balance_normalized)) * Decimal("100")

            sections[account.account_type].append(
                BalanceSheetAccountRow(
                    account_code=account.code,
                    account_name=account.name,
                    account_type=account.account_type,
                    balance=normalized,
                    raw_balance=balance,
                    transaction_count=count,
                    comparison_balance=comparison_balance_normalized,
                    change_amount=change_amount,
                    change_percent=change_percent,
                )
            )

        for rows in sections.values():
            rows.sort(key=lambda item: (abs(item.balance), item.account_code), reverse=True)

        return sections

    @staticmethod
    def _sum_balances(rows: Iterable[BalanceSheetAccountRow]) -> Decimal:
        """Sum normalized balances for a section."""
        total = Decimal("0")
        for row in rows:
            total += row.balance
        return total
