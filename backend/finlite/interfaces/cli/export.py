"""
Export commands - Export financial data to various formats.

Commands:
    fin export beancount  - Export ledger to Beancount format
"""

from datetime import datetime
from pathlib import Path
from typing import Annotated, Callable, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from finlite.application.use_cases.export_beancount import (
    ExportBeancountUseCase,
    ExportBeancountCommand,
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
    Register export commands to the Typer app.

    Args:
        app: Typer app instance
        get_container: Function to get DI container
    """

    @app.command("beancount")
    def export_beancount(
        output_path: Annotated[
            Path,
            typer.Argument(
                help="Output file path (e.g., ~/ledger.beancount)",
            ),
        ],
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
            typer.Option("--currency", "-c", help="Operating currency (BRL, USD, etc)"),
        ] = "USD",
        include_metadata: Annotated[
            bool,
            typer.Option("--metadata/--no-metadata", help="Include tags and metadata"),
        ] = True,
    ):
        """
        Export ledger to Beancount plain-text format.

        Beancount is a double-entry accounting system that uses plain text files.
        This command exports all accounts and transactions in Beancount format.

        Learn more: https://beancount.github.io/

        Examples:
            $ fin export beancount ~/ledger.beancount
            $ fin export beancount ledger.txt --from 2025-01-01 --to 2025-12-31
            $ fin export beancount output.beancount --currency BRL
            $ fin export beancount ledger.beancount --no-metadata
        """
        container = get_container()
        use_case: ExportBeancountUseCase = container.export_beancount_use_case()

        # Parse dates
        from_dt = None
        to_dt = None

        try:
            if from_date:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            if to_date:
                to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError as e:
            console.print(f"[red]Invalid date format:[/red] {e}")
            console.print("[dim]Use YYYY-MM-DD format (e.g., 2025-10-01)[/dim]")
            raise typer.Exit(code=1)

        console.print("[cyan]Exporting to Beancount format...[/cyan]")

        if from_dt or to_dt:
            date_range = f"{from_dt.date() if from_dt else 'start'} to {to_dt.date() if to_dt else 'end'}"
            console.print(f"[dim]Date range: {date_range}[/dim]")

        try:
            # Execute use case
            command = ExportBeancountCommand(
                output_path=output_path,
                from_date=from_dt,
                to_date=to_dt,
                operating_currency=currency.upper(),
                include_metadata=include_metadata,
            )

            result = use_case.execute(command)

            # Show success
            console.print()
            console.print(Panel.fit(
                f"[green]✓ Export successful![/green]\n\n"
                f"[bold]Output:[/bold] {result.output_path}\n"
                f"[bold]Accounts:[/bold] {result.accounts_count}\n"
                f"[bold]Transactions:[/bold] {result.transactions_count}\n"
                f"[bold]File Size:[/bold] {result.file_size_bytes:,} bytes",
                title="Export Complete",
                border_style="green",
            ))

            # Next steps
            console.print()
            console.print("[dim]Next steps:[/dim]")
            console.print(f"  • Validate: [cyan]bean-check {result.output_path}[/cyan]")
            console.print(f"  • View reports: [cyan]bean-report {result.output_path} balances[/cyan]")
            console.print(f"  • Web interface: [cyan]bean-web {result.output_path}[/cyan]")
            console.print()
            console.print("[dim]Learn more about Beancount at https://beancount.github.io/[/dim]")

        except FileNotFoundError as e:
            console.print(f"[red]✗ Path not found:[/red] {e}")
            console.print("[dim]Make sure the parent directory exists[/dim]")
            raise typer.Exit(code=1)

        except Exception as e:
            console.print(f"[red]✗ Export failed:[/red] {e}")
            logger.error("export_beancount_failed", output=str(output_path), error=str(e), exc_info=True)
            raise typer.Exit(code=1)
