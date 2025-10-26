"""Build Credit Card Statement use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple

from finlite.domain.entities.card_statement import (
    CardStatementItem,
    CardStatementRecord,
    StatementStatus,
)
from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.card_statement_repository import ICardStatementRepository
from finlite.domain.repositories.transaction_repository import ITransactionRepository
from finlite.domain.value_objects.account_type import AccountType
from finlite.infrastructure.persistence.unit_of_work import UnitOfWork

EARLIEST_DATETIME = datetime(2000, 1, 1)


@dataclass(frozen=True)
class BuildCardStatementCommand:
    """Command to generate credit card statement for a given period (YYYY-MM)."""

    card_account_code: str
    period: date  # First day of the reference month
    currency: str = "BRL"


@dataclass(frozen=True)
class StatementChargeView:
    """Presentation-friendly statement item."""

    occurred_at: datetime
    description: str
    amount: Decimal
    category_code: str
    category_name: str
    transaction_id: str
    installment_number: Optional[int] = None
    installment_total: Optional[int] = None
    installment_key: Optional[str] = None


@dataclass(frozen=True)
class CardStatementResult:
    """Result returned to CLI layer."""

    statement_id: str
    card_account_code: str
    card_account_name: str
    period_start: date
    period_end: date
    due_date: date
    closing_day: int
    currency: str
    previous_balance: Decimal
    charges_total: Decimal
    total_due: Decimal
    status: StatementStatus
    items: tuple[StatementChargeView, ...]


class BuildCardStatementUseCase:
    """Generates and persists a credit card statement for a billing cycle."""

    def __init__(
        self,
        uow: UnitOfWork,
        account_repository: IAccountRepository,
        transaction_repository: ITransactionRepository,
        card_statement_repository: ICardStatementRepository,
    ) -> None:
        self._uow = uow
        self._account_repository = account_repository
        self._transaction_repository = transaction_repository
        self._card_statement_repository = card_statement_repository

    def execute(self, command: BuildCardStatementCommand) -> CardStatementResult:
        with self._uow:
            card_account = self._account_repository.find_by_code(command.card_account_code)
            if not card_account:
                raise ValueError(f"Card account not found: {command.card_account_code}")

            if card_account.account_type != AccountType.LIABILITY:
                raise ValueError("Credit card statements require a LIABILITY account")

            if not card_account.has_card_metadata():
                raise ValueError(
                    "Credit card metadata (issuer, closing day, due day) must be configured"
                )

            period_start, period_end, due_date = self._compute_period(
                command.period,
                card_account.card_closing_day,
                card_account.card_due_day,
            )

            existing = self._card_statement_repository.find_by_period(
                card_account_id=card_account.id,
                period_start=period_start,
                period_end=period_end,
            )

            items, charges_total = self._collect_items(
                card_account_id=card_account.id,
                period_start=period_start,
                period_end=period_end,
                currency=command.currency,
            )

            previous_balance = self._calculate_previous_balance(
                card_account_id=card_account.id,
                period_start=period_start,
                currency=command.currency,
            )

            total_due = previous_balance + charges_total

            if existing:
                record = CardStatementRecord(
                    id=existing.id,
                    card_account_id=existing.card_account_id,
                    period_start=period_start,
                    period_end=period_end,
                    closing_day=card_account.card_closing_day,
                    due_date=due_date,
                    currency=command.currency,
                    total_amount=charges_total,
                    items=tuple(items),
                    status=existing.status,
                    created_at=existing.created_at,
                    updated_at=datetime.utcnow(),
                )
            else:
                record = CardStatementRecord.create(
                    card_account_id=card_account.id,
                    period_start=period_start,
                    period_end=period_end,
                    closing_day=card_account.card_closing_day,
                    due_date=due_date,
                    currency=command.currency,
                    items=items,
                    total_amount=charges_total,
                )

            saved = self._card_statement_repository.save(record)

            return CardStatementResult(
                statement_id=str(saved.id),
                card_account_code=card_account.code,
                card_account_name=card_account.name,
                period_start=period_start,
                period_end=period_end,
                due_date=due_date,
                closing_day=card_account.card_closing_day,
                currency=command.currency,
                previous_balance=previous_balance,
                charges_total=charges_total,
                total_due=total_due,
                status=saved.status,
                items=tuple(
                    StatementChargeView(
                        occurred_at=item.occurred_at,
                        description=item.description,
                        amount=item.amount,
                        category_code=item.category_code,
                        category_name=item.category_name,
                        transaction_id=str(item.transaction_id),
                        installment_number=item.installment_number,
                        installment_total=item.installment_total,
                        installment_key=item.installment_key,
                    )
                    for item in saved.items
                ),
            )

    # ------------------------------------------------------------------ helpers

    def _compute_period(
        self,
        period_anchor: date,
        closing_day: int,
        due_day: int,
    ) -> Tuple[date, date, date]:
        year = period_anchor.year
        month = period_anchor.month

        period_end = self._coerce_day(date(year, month, 1), closing_day)
        previous_month = (period_end.replace(day=1) - timedelta(days=1)).replace(day=1)
        period_start = self._coerce_day(previous_month, closing_day) + timedelta(days=1)

        due_month = month
        due_year = year
        if due_day <= closing_day:
            # due date is in the following month
            if month == 12:
                due_month = 1
                due_year += 1
            else:
                due_month += 1
        due_date = self._coerce_day(date(due_year, due_month, 1), due_day)
        return period_start, period_end, due_date

    def _coerce_day(self, base: date, target_day: int) -> date:
        last_day = self._last_day_of_month(base.year, base.month)
        day = min(target_day, last_day.day)
        return base.replace(day=day)

    def _last_day_of_month(self, year: int, month: int) -> date:
        if month == 12:
            return date(year, 12, 31)
        next_month = date(year, month + 1, 1)
        return next_month - timedelta(days=1)

    def _collect_items(
        self,
        card_account_id: UUID,
        period_start: date,
        period_end: date,
        currency: str,
    ) -> tuple[list[CardStatementItem], Decimal]:
        transactions = self._transaction_repository.find_by_date_range(
            start_date=datetime.combine(period_start, datetime.min.time()),
            end_date=datetime.combine(period_end, datetime.max.time()),
        )

        all_accounts = {acc.id: acc for acc in self._account_repository.list_all()}
        items: list[CardStatementItem] = []
        total = Decimal("0")

        for txn in transactions:
            if not txn.has_account(card_account_id):
                continue

            installment_number, installment_total, installment_key = self._parse_installment(txn.tags or ())
            card_postings = txn.get_postings_for_account(card_account_id)

            for posting in card_postings:
                if posting.amount.currency.upper() != currency.upper():
                    continue
                if posting.is_credit():  # purchase
                    other_posting = next((p for p in txn.postings if p.account_id != card_account_id), None)
                    category_code = "Unknown"
                    category_name = "Unknown"
                    if other_posting:
                        account = all_accounts.get(other_posting.account_id)
                        if account:
                            category_code = account.code
                            category_name = account.name

                    amount = abs(posting.amount.amount)
                    total += amount
                    items.append(
                        CardStatementItem(
                            transaction_id=txn.id,
                            occurred_at=datetime.combine(txn.date, datetime.min.time()),
                            description=txn.description,
                            amount=amount,
                            currency=posting.amount.currency,
                            category_code=category_code,
                            category_name=category_name,
                            installment_number=installment_number,
                            installment_total=installment_total,
                            installment_key=installment_key,
                        )
                    )

        items.sort(key=lambda item: item.occurred_at)
        return items, total

    def _calculate_previous_balance(
        self,
        card_account_id: UUID,
        period_start: date,
        currency: str,
    ) -> Decimal:
        if period_start <= date(2000, 1, 1):
            return Decimal("0")

        preceding_transactions = self._transaction_repository.find_by_date_range(
            start_date=EARLIEST_DATETIME,
            end_date=datetime.combine(period_start - timedelta(days=1), datetime.max.time()),
        )
        balance = Decimal("0")
        for txn in preceding_transactions:
            if not txn.has_account(card_account_id):
                continue
            for posting in txn.get_postings_for_account(card_account_id):
                if posting.amount.currency.upper() != currency.upper():
                    continue
                balance += -posting.amount.amount
        return balance

    def _parse_installment(self, tags: tuple[str, ...]) -> tuple[Optional[int], Optional[int], Optional[str]]:
        number = total = None
        key = None
        for tag in tags:
            if tag.startswith("card:installment="):
                payload = tag.split("=", 1)[1]
                if "/" in payload:
                    current_str, total_str = payload.split("/", 1)
                    try:
                        number = int(current_str)
                        total = int(total_str)
                    except ValueError:
                        number = total = None
            elif tag.startswith("card:installment_key="):
                key = tag.split("=", 1)[1]
        return number, total, key
