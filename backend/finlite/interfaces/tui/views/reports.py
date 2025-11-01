"""Reporting views for TUI."""

from __future__ import annotations

from datetime import datetime, timedelta

from textual.widgets import Static

from finlite.application.use_cases.generate_cashflow_report import (
    GenerateCashflowCommand,
    GenerateCashflowReportUseCase,
)


class ReportsView(Static):
    """Simple reports container."""

    DEFAULT_CSS = """
    ReportsView {
        padding: 1 2;
    }
    """

    def show_cashflow(self, container) -> None:
        use_case: GenerateCashflowReportUseCase = container.generate_cashflow_report_use_case()
        today = datetime.now()
        start = (today - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        report = use_case.execute(
            GenerateCashflowCommand(
                from_date=start,
                to_date=today,
                currency="BRL",
            )
        )

        lines = [
            "# Cashflow Report (Last 30 days)",
            f"Total Income: {report.total_income:,.2f} {report.currency}",
            f"Total Expenses: {report.total_expenses:,.2f} {report.currency}",
            f"Net Cashflow: {report.net_cashflow:,.2f} {report.currency}",
            "",
            "## Top Expense Categories",
        ]
        if report.expense_categories:
            for item in report.expense_categories[:5]:
                lines.append(
                    f"- {item.account_code}: {abs(item.amount):,.2f} ({item.transaction_count} tx)"
                )
        else:
            lines.append("(no expenses recorded)")

        self.update("\n".join(lines))
