"""Dashboard view for the Finlite TUI."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from textual.widgets import Static

from ..services import DashboardSummary


class DashboardView(Static):
    """Simple dashboard summary view."""

    DEFAULT_CSS = """
    DashboardView {
        padding: 1 2;
    }
    """

    def show_summary(self, summary: DashboardSummary) -> None:
        recent_lines = "\n".join(
            f"- {date:%Y-%m-%d}: {description} ({amount:,.2f} {currency})"
            for date, description, amount, currency in summary.recent_transactions
        ) or "(no transactions yet)"

        expense_lines = "\n".join(
            f"- {code}: {amount:,.2f}"
            for code, amount in summary.top_expenses
        ) or "(no expenses recorded)"

        text = (
            "# Dashboard\n\n"
            f"**Accounts:** {summary.total_accounts}\n\n"
            f"**Pending Entries:** {summary.pending_entries}\n\n"
            f"**Net Cashflow:** {summary.cashflow_net:,.2f} BRL\n\n"
            "## Top Expense Categories\n"
            f"{expense_lines}\n\n"
            f"## Recent Transactions\n{recent_lines}\n"
        )
        self.update(text)
