"""
Reports commands - Generate financial reports.

Commands:
    fin report balance-sheet  - Generate balance sheet snapshot
    fin report cashflow       - Generate cashflow report
"""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
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
from finlite.application.use_cases.generate_income_statement_report import (
    GenerateIncomeStatementReportUseCase,
    GenerateIncomeStatementCommand,
    ComparisonMode,
    IncomeStatementAccountRow,
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

    @app.command("income-statement")
    def income_statement_report(
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
        compare: Annotated[
            Optional[str],
            typer.Option(
                "--compare",
                help="Comparison mode: 'previous' (previous period) or 'yoy' (year-over-year)",
            ),
        ] = None,
        export: Annotated[
            Optional[str],
            typer.Option(
                "--export",
                help="Export to file (CSV or Markdown): e.g., report.csv or report.md",
            ),
        ] = None,
        chart: Annotated[
            bool,
            typer.Option("--chart", help="Show visual chart of revenue vs expenses"),
        ] = False,
    ):
        """
        Generate income statement (profit & loss) report for a period.

        Shows revenues, expenses, and net income. Optionally compare to previous period
        or year-over-year (YoY).

        Examples:
            $ fin report income-statement --from 2025-01-01 --to 2025-12-31
            $ fin report income-statement --from 2025-10-01 --to 2025-10-31 --compare previous
            $ fin report income-statement --from 2025-10-01 --to 2025-10-31 --compare yoy
            $ fin report income-statement --from 2025-10-01 --to 2025-10-31 --export report.csv
            $ fin report income-statement --from 2025-10-01 --to 2025-10-31 --chart
        """
        container = get_container()
        use_case: GenerateIncomeStatementReportUseCase = (
            container.generate_income_statement_report_use_case()
        )

        # Parse dates
        try:
            from_dt = (
                datetime.strptime(from_date, "%Y-%m-%d").date()
                if from_date
                else datetime(datetime.now().year, 1, 1).date()
            )
            to_dt = (
                datetime.strptime(to_date, "%Y-%m-%d").date()
                if to_date
                else datetime.now().date()
            )
        except ValueError as e:
            console.print(f"[red]Invalid date format:[/red] {e}")
            console.print("[dim]Use YYYY-MM-DD format (e.g., 2025-10-01)[/dim]")
            raise typer.Exit(code=1)

        # Parse comparison mode
        comparison_mode = ComparisonMode.NONE
        if compare:
            compare_lower = compare.lower()
            if compare_lower in ("previous", "prev", "p"):
                comparison_mode = ComparisonMode.PREVIOUS_PERIOD
            elif compare_lower in ("yoy", "year-over-year", "yearly", "y"):
                comparison_mode = ComparisonMode.YEAR_OVER_YEAR
            else:
                console.print(
                    f"[red]Invalid comparison mode:[/red] {compare}\n"
                    "[dim]Use 'previous' or 'yoy'[/dim]"
                )
                raise typer.Exit(code=1)

        console.print("[cyan]Generating income statement report...[/cyan]")
        console.print(
            f"[dim]Period: {from_dt.isoformat()} to {to_dt.isoformat()} | Currency: {currency.upper()}[/dim]"
        )

        def _format_amount(
            amount: Decimal, curr: str, positive_style: str = "green"
        ) -> str:
            style = positive_style if amount >= 0 else "red"
            return f"[{style}]{amount:,.2f}[/{style}] {curr}"

        def _format_comparison(row: IncomeStatementAccountRow) -> str:
            """Format comparison data if available."""
            if row.comparison_amount is None:
                return ""

            change_icon = "▲" if row.change_amount >= 0 else "▼"
            change_color = "green" if row.change_amount >= 0 else "red"

            return (
                f"[dim]{row.comparison_amount:,.2f}[/dim] → "
                f"[{change_color}]{change_icon} {abs(row.change_amount):,.2f} "
                f"({row.change_percent:+.1f}%)[/{change_color}]"
            )

        def _render_section(
            title: str,
            rows: list[IncomeStatementAccountRow],
            total: Decimal,
            positive_style: str,
            show_comparison: bool = False,
        ) -> None:
            if not rows:
                return

            table = Table(
                title=title,
                show_header=True,
                header_style=f"bold {positive_style}",
            )
            table.add_column("Account", style="cyan", no_wrap=True)
            table.add_column("Amount", justify="right", style=positive_style)
            table.add_column("% of Revenue", justify="right", style="dim")
            table.add_column("Txns", justify="right", style="dim")

            if show_comparison:
                table.add_column("Comparison", justify="right", style="dim")

            revenue_total = result.revenue_total if result.revenue_total > 0 else Decimal("1")

            for row in rows:
                percent_of_revenue = (row.amount / revenue_total * Decimal("100"))
                columns = [
                    row.account_code,
                    _format_amount(row.amount, result.currency, positive_style),
                    f"{percent_of_revenue:.1f}%",
                    str(row.transaction_count),
                ]

                if show_comparison:
                    columns.append(_format_comparison(row))

                table.add_row(*columns)

            # Add total row
            total_columns = [
                f"[bold]Total {title}[/bold]",
                f"[bold]{_format_amount(total, result.currency, positive_style)}[/bold]",
                "",
                "",
            ]
            if show_comparison:
                total_columns.append("")
            table.add_row(*total_columns)

            console.print()
            console.print(table)

        def _export_to_csv(filename: str) -> None:
            """Export report to CSV file."""
            path = Path(filename)
            with path.open("w", newline="") as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(["Income Statement Report"])
                writer.writerow(
                    [
                        f"Period: {result.from_date} to {result.to_date}",
                        f"Currency: {result.currency}",
                    ]
                )
                writer.writerow([])

                # Revenue section
                writer.writerow(["REVENUE"])
                writer.writerow(["Account Code", "Account Name", "Amount", "Transactions"])
                for row in result.revenue:
                    writer.writerow(
                        [row.account_code, row.account_name, f"{row.amount:.2f}", row.transaction_count]
                    )
                writer.writerow(["Total Revenue", "", f"{result.revenue_total:.2f}", ""])
                writer.writerow([])

                # Expenses section
                writer.writerow(["EXPENSES"])
                writer.writerow(["Account Code", "Account Name", "Amount", "Transactions"])
                for row in result.expenses:
                    writer.writerow(
                        [row.account_code, row.account_name, f"{row.amount:.2f}", row.transaction_count]
                    )
                writer.writerow(["Total Expenses", "", f"{result.expenses_total:.2f}", ""])
                writer.writerow([])

                # Net income
                writer.writerow(["NET INCOME", "", f"{result.net_income:.2f}", ""])

            console.print(f"[green]✓ Report exported to:[/green] {path.absolute()}")

        def _export_to_markdown(filename: str) -> None:
            """Export report to Markdown file."""
            path = Path(filename)
            with path.open("w") as f:
                f.write(f"# Income Statement Report\n\n")
                f.write(f"**Period:** {result.from_date} to {result.to_date}  \n")
                f.write(f"**Currency:** {result.currency}  \n\n")

                # Revenue section
                f.write("## Revenue\n\n")
                f.write("| Account Code | Account Name | Amount | Transactions |\n")
                f.write("|--------------|--------------|--------|-------------|\n")
                for row in result.revenue:
                    f.write(
                        f"| {row.account_code} | {row.account_name} | "
                        f"{row.amount:,.2f} | {row.transaction_count} |\n"
                    )
                f.write(
                    f"| **Total Revenue** | | **{result.revenue_total:,.2f}** | |\n\n"
                )

                # Expenses section
                f.write("## Expenses\n\n")
                f.write("| Account Code | Account Name | Amount | Transactions |\n")
                f.write("|--------------|--------------|--------|-------------|\n")
                for row in result.expenses:
                    f.write(
                        f"| {row.account_code} | {row.account_name} | "
                        f"{row.amount:,.2f} | {row.transaction_count} |\n"
                    )
                f.write(
                    f"| **Total Expenses** | | **{result.expenses_total:,.2f}** | |\n\n"
                )

                # Net income
                f.write("## Summary\n\n")
                f.write(f"| Metric | Amount |\n")
                f.write(f"|--------|--------|\n")
                f.write(f"| Total Revenue | {result.revenue_total:,.2f} |\n")
                f.write(f"| Total Expenses | {result.expenses_total:,.2f} |\n")
                f.write(f"| **Net Income** | **{result.net_income:,.2f}** |\n")

            console.print(f"[green]✓ Report exported to:[/green] {path.absolute()}")

        def _show_chart() -> None:
            """Show a simple ASCII chart of revenue vs expenses."""
            from rich.bar_chart import BarChart

            chart_data = {
                "Revenue": float(result.revenue_total),
                "Expenses": float(result.expenses_total),
                "Net Income": float(result.net_income),
            }

            console.print()
            console.print("[bold]Revenue vs Expenses Chart[/bold]")

            # Simple text-based visualization
            max_val = max(float(result.revenue_total), float(result.expenses_total))
            if max_val > 0:
                revenue_bar = "█" * int((float(result.revenue_total) / max_val) * 50)
                expense_bar = "█" * int((float(result.expenses_total) / max_val) * 50)

                console.print()
                console.print(f"[green]Revenue  ({result.revenue_total:,.2f}):[/green]")
                console.print(f"[green]{revenue_bar}[/green]")
                console.print()
                console.print(f"[red]Expenses ({result.expenses_total:,.2f}):[/red]")
                console.print(f"[red]{expense_bar}[/red]")
                console.print()

                net_color = "green" if result.net_income >= 0 else "red"
                console.print(f"[{net_color}]Net Income: {result.net_income:,.2f}[/{net_color}]")

        try:
            command = GenerateIncomeStatementCommand(
                from_date=from_dt,
                to_date=to_dt,
                currency=currency.upper(),
                comparison_mode=comparison_mode,
            )
            result = use_case.execute(command)

            # Display summary panel
            console.print()
            summary_lines = [
                f"[bold]Period:[/bold] {result.from_date} to {result.to_date}",
                f"[bold]Currency:[/bold] {result.currency}",
                "",
                f"[bold]Total Revenue:[/bold] [green]{result.revenue_total:,.2f}[/green] {result.currency}",
                f"[bold]Total Expenses:[/bold] [red]{result.expenses_total:,.2f}[/red] {result.currency}",
            ]

            net_color = "green" if result.net_income >= 0 else "red"
            summary_lines.append(
                f"[bold]Net Income:[/bold] [{net_color}]{result.net_income:,.2f}[/{net_color}] {result.currency}"
            )

            if comparison_mode != ComparisonMode.NONE and result.comparison_net_income is not None:
                summary_lines.append("")
                summary_lines.append(
                    f"[dim]Comparison Period: {result.comparison_from_date} to {result.comparison_to_date}[/dim]"
                )
                comp_net_change = result.net_income - result.comparison_net_income
                comp_net_pct = (
                    (comp_net_change / result.comparison_net_income * Decimal("100"))
                    if result.comparison_net_income != 0
                    else Decimal("0")
                )
                change_icon = "▲" if comp_net_change >= 0 else "▼"
                change_color = "green" if comp_net_change >= 0 else "red"
                summary_lines.append(
                    f"[dim]Net Income Change:[/dim] [{change_color}]{change_icon} {abs(comp_net_change):,.2f} "
                    f"({comp_net_pct:+.1f}%)[/{change_color}]"
                )

            console.print(
                Panel.fit(
                    "\n".join(summary_lines),
                    title="Income Statement Summary",
                    border_style="cyan",
                )
            )

            # Display detailed sections
            show_comparison = comparison_mode != ComparisonMode.NONE
            _render_section(
                "Revenue", result.revenue, result.revenue_total, "green", show_comparison
            )
            _render_section(
                "Expenses", result.expenses, result.expenses_total, "red", show_comparison
            )

            # Empty state
            if not result.revenue and not result.expenses:
                console.print()
                console.print("[yellow]No income or expense data found for the selected period.[/yellow]")
                console.print("[dim]Try a different date range or import more data[/dim]")

            # Handle export
            if export:
                export_path = Path(export)
                if export_path.suffix.lower() == ".csv":
                    _export_to_csv(export)
                elif export_path.suffix.lower() == ".md":
                    _export_to_markdown(export)
                else:
                    console.print(
                        f"[yellow]Warning:[/yellow] Unknown export format '{export_path.suffix}'. "
                        f"Supported: .csv, .md"
                    )

            # Handle chart
            if chart:
                _show_chart()

        except Exception as exc:
            console.print(f"[red]✗ Failed to generate report:[/red] {exc}")
            logger.error("income_statement_report_failed", error=str(exc), exc_info=True)
            raise typer.Exit(code=1)
