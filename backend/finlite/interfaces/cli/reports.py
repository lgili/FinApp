"""
Reports commands - Generate financial reports.

Commands:
    fin report balance-sheet  - Generate balance sheet snapshot
    fin report cashflow       - Generate cashflow report
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Callable, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from finlite.application.use_cases.generate_balance_sheet_report import (
    GenerateBalanceSheetReportUseCase,
    GenerateBalanceSheetCommand,
    BalanceSheetAccountRow,
)
from finlite.application.use_cases.generate_cashflow_report import (
    GenerateCashflowReportUseCase,
    GenerateCashflowCommand,
)
from finlite.shared.di import Container
from finlite.shared.observability import get_logger

logger = get_logger(__name__)
console = Console()


def register_commands(
    app: typer.Typer,
    get_container: Callable[[], Container],
) -> None:
    """
    Register report commands to the Typer app.

    Args:
        app: Typer app instance
        get_container: Function to get DI container
    """

    @app.command("balance-sheet")
    def balance_sheet_report(
        at: Annotated[
            Optional[str],
            typer.Option("--at", help="Effective date (YYYY-MM-DD)"),
        ] = None,
        currency: Annotated[
            str,
            typer.Option("--currency", "-c", help="Currency for report (BRL, USD, etc)"),
        ] = "BRL",
        details: Annotated[
            bool,
            typer.Option(
                "--details/--summary",
                help="Show per-account breakdown tables",
            ),
        ] = True,
    ):
        """
        Generate a balance sheet snapshot as of a specific date.

        Summarizes totals for Assets, Liabilities, and Equity and optionally
        renders per-account breakdown tables.
        """
        container = get_container()
        use_case: GenerateBalanceSheetReportUseCase = (
            container.generate_balance_sheet_report_use_case()
        )

        # Parse date input
        try:
            as_of = (
                datetime.strptime(at, "%Y-%m-%d").date() if at else datetime.now().date()
            )
        except ValueError as exc:
            console.print(f"[red]Invalid date format:[/red] {exc}")
            console.print("[dim]Use YYYY-MM-DD format (e.g., 2025-10-31)[/dim]")
            raise typer.Exit(code=1)

        console.print("[cyan]Generating balance sheet report...[/cyan]")
        console.print(
            f"[dim]As of: {as_of.isoformat()} | Currency: {currency.upper()}[/dim]"
        )

        def _format_amount(amount: Decimal, curr: str, positive_style: str = "green") -> str:
            style = positive_style if amount >= 0 else "red"
            return f"[{style}]{amount:,.2f}[/{style}] {curr}"

        def _render_section(
            title: str,
            rows: list[BalanceSheetAccountRow],
            positive_style: str,
        ) -> None:
            if not details or not rows:
                return

            table = Table(
                title=title,
                show_header=True,
                header_style=f"bold {positive_style}",
            )
            table.add_column("Account", style="cyan", no_wrap=True)
            table.add_column("Balance", justify="right", style=positive_style)
            table.add_column("Postings", justify="right", style="dim")

            for row in rows:
                table.add_row(
                    row.account_code,
                    _format_amount(row.balance, result.currency, positive_style),
                    str(row.transaction_count),
                )

            console.print()
            console.print(table)

        try:
            command = GenerateBalanceSheetCommand(
                as_of=as_of,
                currency=currency.upper(),
            )
            result = use_case.execute(command)

            console.print()
            summary_table = Table(
                title=f"Balance Sheet — {result.as_of.isoformat()}",
                show_header=False,
                header_style="bold",
            )
            summary_table.add_column("Section", style="cyan", no_wrap=True)
            summary_table.add_column("Total", justify="right", style="bold")

            summary_table.add_row(
                "Assets",
                _format_amount(result.assets_total, result.currency, "green"),
            )
            summary_table.add_row(
                "Liabilities",
                _format_amount(result.liabilities_total, result.currency, "yellow"),
            )
            summary_table.add_row(
                "Equity",
                _format_amount(result.equity_total, result.currency, "blue"),
            )
            summary_table.add_row(
                "Net Worth",
                _format_amount(result.net_worth, result.currency, "green"),
            )

            console.print(summary_table)

            if not (result.assets or result.liabilities or result.equity):
                console.print()
                console.print("[yellow]No balance sheet data found for the selected date.[/yellow]")
                return

            _render_section("Asset Accounts", result.assets, "green")
            _render_section("Liability Accounts", result.liabilities, "yellow")
            _render_section("Equity Accounts", result.equity, "blue")

        except Exception as exc:
            console.print(f"[red]✗ Failed to generate report:[/red] {exc}")
            logger.error("balance_sheet_report_failed", error=str(exc), exc_info=True)
            raise typer.Exit(code=1)

    @app.command("cashflow")
    def cashflow_report(
        from_date: Annotated[
            Optional[str],
            typer.Option("--from", "-f", help="Start date (YYYY-MM-DD)"),
        ] = None,
        to_date: Annotated[
            Optional[str],
            typer.Option("--to", "-t", help="End date (YYYY-MM-DD)"),
        ] = None,
        currency: Annotated[
            str,
            typer.Option("--currency", "-c", help="Currency for report (BRL, USD, etc)"),
        ] = "BRL",
        account_filter: Annotated[
            Optional[str],
            typer.Option("--account", "-a", help="Filter by account prefix (e.g., Expenses:Food)"),
        ] = None,
        show_assets: Annotated[
            bool,
            typer.Option("--show-assets", help="Show asset balances in report"),
        ] = True,
    ):
        """
        Generate cashflow report for a period.

        Shows income, expenses, and net cashflow aggregated by account.
        Useful for understanding spending patterns and cash flow.

        Examples:
            $ fin report cashflow
            $ fin report cashflow --from 2025-10-01 --to 2025-10-31
            $ fin report cashflow --currency USD
            $ fin report cashflow --account Expenses:Food
            $ fin report cashflow --no-show-assets
        """
        container = get_container()
        use_case: GenerateCashflowReportUseCase = container.generate_cashflow_report_use_case()

        # Parse dates
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime(2000, 1, 1)
            to_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime.now()
        except ValueError as e:
            console.print(f"[red]Invalid date format:[/red] {e}")
            console.print("[dim]Use YYYY-MM-DD format (e.g., 2025-10-01)[/dim]")
            raise typer.Exit(code=1)

        console.print(f"[cyan]Generating cashflow report...[/cyan]")
        console.print(f"[dim]Period: {from_dt.date()} to {to_dt.date()}[/dim]")

        try:
            # Execute use case
            command = GenerateCashflowCommand(
                from_date=from_dt,
                to_date=to_dt,
                currency=currency.upper(),
                account_code_filter=account_filter,
            )

            result = use_case.execute(command)

            # Show summary
            console.print()
            console.print(Panel.fit(
                f"[bold]Period:[/bold] {result.from_date.date()} to {result.to_date.date()}\n"
                f"[bold]Currency:[/bold] {result.currency}\n\n"
                f"[bold]Total Income:[/bold] [green]{result.total_income:,.2f}[/green] {result.currency}\n"
                f"[bold]Total Expenses:[/bold] [red]{result.total_expenses:,.2f}[/red] {result.currency}\n"
                f"[bold]Net Cashflow:[/bold] {'[green]' if result.net_cashflow >= 0 else '[red]'}{result.net_cashflow:,.2f}{'[/green]' if result.net_cashflow >= 0 else '[/red]'} {result.currency}",
                title="Cashflow Summary",
                border_style="cyan",
            ))

            # Income table
            if result.income_categories:
                console.print()
                income_table = Table(
                    title=f"Income by Category ({len(result.income_categories)} categories)",
                    show_header=True,
                    header_style="bold green",
                )

                income_table.add_column("Account", style="cyan", width=40)
                income_table.add_column("Amount", justify="right", style="green", width=20)
                income_table.add_column("Transactions", justify="right", style="dim", width=15)
                income_table.add_column("% of Total", justify="right", style="yellow", width=12)

                for item in result.income_categories:
                    percentage = (abs(item.amount) / result.total_income * 100) if result.total_income > 0 else 0
                    income_table.add_row(
                        item.account_code,
                        f"{abs(item.amount):,.2f}",
                        str(item.transaction_count),
                        f"{percentage:.1f}%",
                    )

                console.print(income_table)

            # Expenses table
            if result.expense_categories:
                console.print()
                expense_table = Table(
                    title=f"Expenses by Category ({len(result.expense_categories)} categories)",
                    show_header=True,
                    header_style="bold red",
                )

                expense_table.add_column("Account", style="cyan", width=40)
                expense_table.add_column("Amount", justify="right", style="red", width=20)
                expense_table.add_column("Transactions", justify="right", style="dim", width=15)
                expense_table.add_column("% of Total", justify="right", style="yellow", width=12)

                for item in result.expense_categories:
                    percentage = (abs(item.amount) / result.total_expenses * 100) if result.total_expenses > 0 else 0
                    expense_table.add_row(
                        item.account_code,
                        f"{abs(item.amount):,.2f}",
                        str(item.transaction_count),
                        f"{percentage:.1f}%",
                    )

                console.print(expense_table)

            # Asset balances table
            if show_assets and result.asset_balances:
                console.print()
                asset_table = Table(
                    title=f"Asset Balances ({len(result.asset_balances)} accounts)",
                    show_header=True,
                    header_style="bold blue",
                )

                asset_table.add_column("Account", style="cyan", width=40)
                asset_table.add_column("Balance", justify="right", style="blue", width=20)
                asset_table.add_column("Transactions", justify="right", style="dim", width=15)

                for item in result.asset_balances:
                    balance_color = "green" if item.amount >= 0 else "red"
                    asset_table.add_row(
                        item.account_code,
                        f"[{balance_color}]{item.amount:,.2f}[/{balance_color}]",
                        str(item.transaction_count),
                    )

                console.print(asset_table)

            # Empty state
            if not result.income_categories and not result.expense_categories:
                console.print()
                console.print("[yellow]No transactions found in this period.[/yellow]")
                console.print("[dim]Try a different date range or import more data[/dim]")

        except Exception as e:
            console.print(f"[red]✗ Failed to generate report:[/red] {e}")
            logger.error("cashflow_report_failed", error=str(e), exc_info=True)
            raise typer.Exit(code=1)
