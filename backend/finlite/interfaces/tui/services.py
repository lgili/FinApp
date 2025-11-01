"""Utility helpers for the Finlite TUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Sequence
from uuid import UUID

from finlite.application.use_cases.list_accounts import ListAccountsUseCase
from finlite.application.use_cases.list_transactions import (
    ListTransactionsUseCase,
)
from finlite.application.use_cases.post_pending_entries import (
    PostPendingEntriesCommand,
    PostPendingEntriesUseCase,
)
from finlite.application.use_cases.generate_cashflow_report import (
    GenerateCashflowCommand,
    GenerateCashflowReportUseCase,
)
from finlite.domain.entities.statement_entry import StatementStatus


@dataclass
class DashboardSummary:
    total_accounts: int
    pending_entries: int
    recent_transactions: list[tuple[date, str, Decimal, str]]
    cashflow_net: Decimal
    top_expenses: list[tuple[str, Decimal]]


@dataclass
class StatementEntryRow:
    id: UUID
    occurred_at: date
    memo: str
    amount: Decimal
    currency: str
    status: str
    suggested_account: str | None


def get_dashboard_summary(container) -> DashboardSummary:
    accounts_uc: ListAccountsUseCase = container.list_accounts_use_case()
    accounts = accounts_uc.execute()

    statement_repo = container.statement_entry_repository()
    pending_entries = statement_repo.find_by_status(StatementStatus.IMPORTED)
    if hasattr(statement_repo, "_session"):
        statement_repo._session.close()  # type: ignore[attr-defined]

    transactions_uc: ListTransactionsUseCase = container.list_transactions_use_case()
    transactions = transactions_uc.execute()
    recent = [
        (txn.date, txn.description, sum(p.amount for p in txn.postings), txn.postings[0].currency)
        for txn in transactions[:5]
    ]

    net = Decimal("0")
    top_expenses: list[tuple[str, Decimal]] = []
    if transactions:
        cashflow_uc: GenerateCashflowReportUseCase = container.generate_cashflow_report_use_case()
        earliest = min(txn.date for txn in transactions)
        cashflow = cashflow_uc.execute(
            GenerateCashflowCommand(
                from_date=datetime.combine(earliest, datetime.min.time()),
                to_date=datetime.combine(date.today(), datetime.max.time()),
                currency="BRL",
            )
        )
        net = cashflow.net_cashflow
        top_expenses = [
            (item.account_code, abs(item.amount))
            for item in cashflow.expense_categories[:5]
        ]

    return DashboardSummary(
        total_accounts=len(accounts),
        pending_entries=len(pending_entries),
        recent_transactions=recent,
        cashflow_net=net,
        top_expenses=top_expenses,
    )


def get_pending_entries(
    container,
    limit: int = 50,
    search: str | None = None,
) -> list[StatementEntryRow]:
    uow = container.unit_of_work()
    with uow:
        accounts = {acc.id: acc.code for acc in uow.accounts.list_all()}

    statement_repo = container.statement_entry_repository()
    entries = statement_repo.find_pending(limit=limit)
    if hasattr(statement_repo, "_session"):
        statement_repo._session.close()  # type: ignore[attr-defined]
    if hasattr(statement_repo, "_session"):
        statement_repo._session.close()  # type: ignore[attr-defined]

    rows: list[StatementEntryRow] = []
    for entry in entries:
        suggested = (
            accounts.get(entry.suggested_account_id) if entry.suggested_account_id else None
        )
        rows.append(
            StatementEntryRow(
                id=entry.id,
                occurred_at=entry.occurred_at,
                memo=entry.memo or entry.external_id,
                amount=entry.amount,
                currency=entry.currency,
                status=entry.status.value,
                suggested_account=suggested,
            )
        )

    if search:
        lowered = search.lower()
        rows = [row for row in rows if lowered in (row.memo or "").lower()]

    return rows


def post_statement_entries(container, entry_ids: Sequence[UUID]) -> None:
    if not entry_ids:
        return
    use_case: PostPendingEntriesUseCase = container.post_pending_entries_use_case()
    use_case.execute(
        PostPendingEntriesCommand(
            entry_ids=tuple(entry_ids),
            auto_post=True,
        )
    )


def get_accounts_tree(container) -> list[tuple[str, str]]:
    accounts_uc: ListAccountsUseCase = container.list_accounts_use_case()
    accounts = accounts_uc.execute()
    return [(account.code, account.type) for account in accounts]
