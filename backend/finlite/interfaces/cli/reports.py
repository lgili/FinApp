"""
Reports commands - Generate financial reports.

Commands:
    fin report cashflow  - Generate cashflow report
"""

from datetime import datetime
from typing import Annotated, Callable, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

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
