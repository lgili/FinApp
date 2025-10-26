"""
Tax commands - Monthly IR reporting.

Usage:
    fin tax monthly --month YYYY-MM [--export csv|markdown] [--output FILE]
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Callable, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from finlite.application.use_cases.generate_monthly_tax_report import (
    GenerateMonthlyTaxReportCommand,
    MonthlyTaxBreakdown,
    MonthlyTaxReportUseCase,
)
from finlite.shared.di import Container
from finlite.shared.observability import get_logger

logger = get_logger(__name__)
console = Console()


def register_commands(app: typer.Typer, get_container: Callable[[], Container]) -> None:
    """
    Register tax-related commands.

    Args:
        app: Typer sub-app for tax commands
        get_container: Callable returning DI container
    """

    @app.command("monthly")
    def monthly_tax_report(
        month: Annotated[
            Optional[str],
            typer.Option(
                "--month",
                "-m",
                help="Reference month (YYYY-MM). Defaults to current month.",
            ),
        ] = None,
        currency: Annotated[
            str,
            typer.Option(
                "--currency",
                "-c",
                help="Currency filter for tax metadata (default: BRL)",
            ),
        ] = "BRL",
        export: Annotated[
            Optional[str],
            typer.Option(
                "--export",
                "-e",
                help="Export format (csv or markdown)",
                metavar="FORMAT",
            ),
        ] = None,
        output: Annotated[
            Optional[Path],
            typer.Option(
                "--output",
                "-o",
                help="Output file path when using --export",
            ),
        ] = None,
    ):
        """
        Generate Brazilian monthly capital gains tax summary.

        Includes sales exemptions, loss carryover, dividends, JCP, and DARF base.
        """
        try:
            target_month = _resolve_month(month)
        except ValueError as exc:
            console.print(f"[red]Invalid month:[/red] {exc}")
            console.print("[dim]Use YYYY-MM format (e.g., 2025-10)[/dim]")
            raise typer.Exit(code=1)

        if export and export.lower() not in {"csv", "markdown"}:
            console.print("[red]Invalid export format.[/red] Use 'csv' or 'markdown'.")
            raise typer.Exit(code=1)

        container = get_container()
        use_case: MonthlyTaxReportUseCase = container.generate_monthly_tax_report_use_case()

        command = GenerateMonthlyTaxReportCommand(
            month=target_month,
            currency=currency.upper(),
        )

        try:
            report = use_case.execute(command)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("monthly_tax_report_failed", error=str(exc), exc_info=True)
            console.print(f"[red]✗ Failed to generate tax report:[/red] {exc}")
            raise typer.Exit(code=1)

        breakdown = report.breakdown
        console.print()
        console.print(
            Panel.fit(
                f"[bold]Month:[/bold] {breakdown.month.strftime('%Y-%m')}\n"
                f"[bold]Currency:[/bold] {breakdown.currency}",
                title="Monthly Tax Report",
                border_style="cyan",
            )
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Amount", justify="right")

        def add_row(label: str, value: Decimal, style: str = "white") -> None:
            table.add_row(label, f"[{style}]{_format_decimal(value)}[/{style}] {breakdown.currency}")

        add_row("Total Sales", breakdown.total_sales, "green")
        add_row("Exempt Sales", breakdown.exempt_sales, "yellow")
        add_row("Gains", breakdown.gains, "green")
        add_row("Losses", breakdown.losses, "red")
        add_row("Loss Carry-In", breakdown.loss_carry_in, "yellow")
        add_row("Loss Applied", breakdown.loss_carry_applied, "yellow")
        add_row("Loss Carry-Out", breakdown.loss_carry_out, "yellow")
        add_row("Taxable Base", breakdown.taxable_base, "green")
        add_row("DARF (15%)", breakdown.darf_tax_due, "green")
        add_row("Withheld Tax", breakdown.withheld_tax, "yellow")
        add_row("DARF Payable", breakdown.darf_tax_payable, "red")
        add_row("Dividends", breakdown.dividends, "blue")
        add_row("JCP", breakdown.jcp, "blue")

        console.print()
        console.print(table)

        if export:
            path = _resolve_export_path(export.lower(), output, breakdown.month)
            if export.lower() == "csv":
                _write_csv(path, breakdown)
            else:
                _write_markdown(path, breakdown)
            console.print(f"[green]✔ Report exported to[/green] {path}")

    def _resolve_month(value: Optional[str]) -> date:
        if value is None:
            now = datetime.now()
            return date(now.year, now.month, 1)
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)

    def _format_decimal(value: Decimal) -> str:
        return f"{value:,.2f}"

    def _resolve_export_path(fmt: str, output: Optional[Path], month: date) -> Path:
        if output:
            return output
        suffix = "csv" if fmt == "csv" else "md"
        filename = f"tax-report-{month.strftime('%Y-%m')}.{suffix}"
        return Path.cwd() / filename

    def _write_csv(path: Path, breakdown: MonthlyTaxBreakdown) -> None:
        import csv

        rows = [
            ("month", breakdown.month.strftime("%Y-%m")),
            ("currency", breakdown.currency),
            ("total_sales", breakdown.total_sales),
            ("exempt_sales", breakdown.exempt_sales),
            ("gains", breakdown.gains),
            ("losses", breakdown.losses),
            ("loss_carry_in", breakdown.loss_carry_in),
            ("loss_carry_applied", breakdown.loss_carry_applied),
            ("loss_carry_out", breakdown.loss_carry_out),
            ("taxable_base", breakdown.taxable_base),
            ("darf_rate", breakdown.darf_rate),
            ("darf_tax_due", breakdown.darf_tax_due),
            ("withheld_tax", breakdown.withheld_tax),
            ("darf_tax_payable", breakdown.darf_tax_payable),
            ("dividends", breakdown.dividends),
            ("jcp", breakdown.jcp),
        ]

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            for key, value in rows:
                writer.writerow([key, f"{value}"])

    def _write_markdown(path: Path, breakdown: MonthlyTaxBreakdown) -> None:
        lines = [
            f"# Monthly Tax Report ({breakdown.month.strftime('%Y-%m')})",
            "",
            "| Metric | Amount |",
            "|--------|--------|",
        ]
        entries = [
            ("Total Sales", breakdown.total_sales),
            ("Exempt Sales", breakdown.exempt_sales),
            ("Gains", breakdown.gains),
            ("Losses", breakdown.losses),
            ("Loss Carry-In", breakdown.loss_carry_in),
            ("Loss Applied", breakdown.loss_carry_applied),
            ("Loss Carry-Out", breakdown.loss_carry_out),
            ("Taxable Base", breakdown.taxable_base),
            ("DARF (15%)", breakdown.darf_tax_due),
            ("Withheld Tax", breakdown.withheld_tax),
            ("DARF Payable", breakdown.darf_tax_payable),
            ("Dividends", breakdown.dividends),
            ("JCP", breakdown.jcp),
        ]
        for label, value in entries:
            lines.append(f"| {label} | {value} {breakdown.currency} |")

        path.write_text("\n".join(lines), encoding="utf-8")
