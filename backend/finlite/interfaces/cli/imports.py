"""
Import commands - Import bank statements from CSV/OFX files.

Commands:
    fin import nubank <file>  - Import Nubank CSV statement
    fin import ofx <file>     - Import OFX bank statement
    fin import list           - List all import batches
    fin import entries <id>   - Show entries from a batch
"""

from pathlib import Path
from typing import Annotated, Callable, Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from finlite.application.use_cases.import_nubank_statement import (
    ImportNubankStatement,
    ImportNubankStatementCommand,
)
from finlite.application.use_cases.import_ofx_statement import (
    ImportOFXStatement,
    ImportOFXStatementCommand,
)
from finlite.domain.entities.import_batch import ImportStatus
from finlite.domain.exceptions import DuplicateImportError
from finlite.shared.di import Container
from finlite.shared.observability import get_logger

logger = get_logger(__name__)
console = Console()


def register_commands(
    app: typer.Typer,
    get_container: Callable[[], Container],
) -> None:
    """
    Register import commands to the Typer app.
    
    Args:
        app: Typer app instance
        get_container: Function to get DI container
    """
    
    @app.command("nubank")
    def import_nubank(
        file_path: Annotated[
            Path,
            typer.Argument(
                help="Path to Nubank CSV file",
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
            ),
        ],
        currency: Annotated[
            str,
            typer.Option("--currency", "-c", help="Default currency (BRL, USD, etc)"),
        ] = "BRL",
        account_hint: Annotated[
            Optional[str],
            typer.Option("--account", "-a", help="Suggested account for entries"),
        ] = None,
    ):
        """
        Import Nubank CSV statement.
        
        The CSV file will be parsed and entries will be created in IMPORTED status.
        You can then review and match them to transactions.
        
        Deduplication: Files with the same SHA256 hash will be rejected.
        
        Examples:
            $ fin import nubank ~/Downloads/nubank-2025-10.csv
            $ fin import nubank statement.csv --currency BRL --account "Assets:Nubank"
        """
        container = get_container()
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        
        console.print(f"[cyan]Importing Nubank statement:[/cyan] {file_path.name}")
        
        try:
            # Execute use case
            command = ImportNubankStatementCommand(
                file_path=file_path,
                default_currency=currency.upper(),
                account_hint=account_hint,
            )
            
            result = use_case.execute(command)
            
            # Show success
            console.print()
            console.print(Panel.fit(
                f"[green]✓ Import successful![/green]\n\n"
                f"[bold]Batch ID:[/bold] {result.batch_id}\n"
                f"[bold]Entries:[/bold] {result.entries_count}\n"
                f"[bold]SHA256:[/bold] {result.file_sha256[:16]}...",
                title="Import Complete",
                border_style="green",
            ))
            
            console.print()
            console.print("[dim]Next steps:[/dim]")
            console.print(f"  • Review entries: [cyan]fin import entries {result.batch_id}[/cyan]")
            console.print("  • Match to transactions: [cyan]fin match auto[/cyan] (coming soon)")
            
        except DuplicateImportError as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            console.print("[dim]This file has already been imported.[/dim]")
            raise typer.Exit(code=1)
        
        except Exception as e:
            console.print(f"[red]✗ Import failed:[/red] {e}")
            logger.error("import_failed", file=str(file_path), error=str(e), exc_info=True)
            raise typer.Exit(code=1)

    @app.command("ofx")
    def import_ofx(
        file_path: Annotated[
            Path,
            typer.Argument(
                help="Path to OFX file",
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
            ),
        ],
        currency: Annotated[
            str,
            typer.Option("--currency", "-c", help="Default currency (BRL, USD, etc)"),
        ] = "BRL",
        account_hint: Annotated[
            Optional[str],
            typer.Option("--account", "-a", help="Suggested account for entries"),
        ] = None,
    ):
        """
        Import OFX bank statement.

        Parses standard OFX format files from banks and creates statement entries
        in IMPORTED status. You can then review and match them to transactions.

        Supports: FITID, DTPOSTED, TRNAMT, NAME, MEMO, CURRENCY fields.

        Deduplication: Files with the same SHA256 hash will be rejected.

        Examples:
            $ fin import ofx ~/Downloads/statement.ofx
            $ fin import ofx bank-statement.ofx --currency BRL --account "Assets:Bank"
            $ fin import ofx ~/Downloads/statement.ofx --currency USD
        """
        container = get_container()
        use_case: ImportOFXStatement = container.import_ofx_statement_use_case()

        console.print(f"[cyan]Importing OFX statement:[/cyan] {file_path.name}")

        try:
            # Execute use case
            command = ImportOFXStatementCommand(
                file_path=file_path,
                default_currency=currency.upper(),
                account_hint=account_hint,
            )

            result = use_case.execute(command)

            # Show success
            console.print()
            console.print(Panel.fit(
                f"[green]✓ Import successful![/green]\n\n"
                f"[bold]Batch ID:[/bold] {result.batch_id}\n"
                f"[bold]Entries:[/bold] {result.entries_count}\n"
                f"[bold]SHA256:[/bold] {result.file_sha256[:16]}...",
                title="Import Complete",
                border_style="green",
            ))

            console.print()
            console.print("[dim]Next steps:[/dim]")
            console.print(f"  • Review entries: [cyan]fin import entries {result.batch_id}[/cyan]")
            console.print("  • Match to transactions: [cyan]fin match auto[/cyan] (coming soon)")

        except DuplicateImportError as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            console.print("[dim]This file has already been imported.[/dim]")
            raise typer.Exit(code=1)

        except Exception as e:
            console.print(f"[red]✗ Import failed:[/red] {e}")
            logger.error("ofx_import_failed", file=str(file_path), error=str(e), exc_info=True)
            raise typer.Exit(code=1)

    @app.command("list")
    def list_imports(
        status: Annotated[
            Optional[str],
            typer.Option("--status", "-s", help="Filter by status (PENDING, COMPLETED, FAILED)"),
        ] = None,
        limit: Annotated[
            int,
            typer.Option("--limit", "-n", help="Number of results to show"),
        ] = 50,
    ):
        """
        List all import batches.
        
        Shows recent imports with their status, entry count, and timestamps.
        
        Examples:
            $ fin import list
            $ fin import list --status COMPLETED
            $ fin import list --limit 10
        """
        container = get_container()
        repo = container.import_batch_repository()
        
        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = ImportStatus(status.upper())
            except ValueError:
                console.print(f"[red]Invalid status:[/red] {status}")
                console.print("[dim]Valid values: PENDING, COMPLETED, FAILED, REVERSED[/dim]")
                raise typer.Exit(code=1)
        
        # Fetch batches
        if status_filter:
            batches = repo.find_by_status(status_filter)[:limit]
        else:
            batches = repo.list_all(limit=limit)
        
        if not batches:
            console.print("[yellow]No import batches found.[/yellow]")
            return
        
        # Create table
        table = Table(
            title=f"Import Batches ({len(batches)} shown)",
            show_header=True,
            header_style="bold cyan",
        )
        
        table.add_column("Batch ID", style="dim", width=38)
        table.add_column("Source", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Entries", justify="right", style="green")
        table.add_column("Filename", style="blue")
        table.add_column("Imported At", style="dim")
        
        for batch in batches:
            # Status color
            status_color = {
                "COMPLETED": "green",
                "PENDING": "yellow",
                "FAILED": "red",
                "REVERSED": "dim",
            }.get(batch.status.value, "white")
            
            table.add_row(
                str(batch.id),
                batch.source.value,
                f"[{status_color}]{batch.status.value}[/{status_color}]",
                str(batch.transaction_count),
                batch.filename or "[dim]n/a[/dim]",
                batch.started_at.strftime("%Y-%m-%d %H:%M") if batch.started_at else "",
            )
        
        console.print()
        console.print(table)
        console.print()
        console.print(f"[dim]Showing {len(batches)} of {len(batches)} batches[/dim]")
    
    @app.command("entries")
    def show_entries(
        batch_id: Annotated[
            str,
            typer.Argument(help="Batch ID (UUID) to show entries from"),
        ],
        status: Annotated[
            Optional[str],
            typer.Option("--status", "-s", help="Filter by status (IMPORTED, MATCHED, POSTED)"),
        ] = None,
        limit: Annotated[
            int,
            typer.Option("--limit", "-n", help="Number of entries to show"),
        ] = 100,
    ):
        """
        Show statement entries from an import batch.
        
        Displays all entries with their amounts, dates, and status.
        
        Examples:
            $ fin import entries 123e4567-e89b-12d3-a456-426614174000
            $ fin import entries <batch-id> --status IMPORTED
            $ fin import entries <batch-id> --limit 20
        """
        container = get_container()
        entry_repo = container.statement_entry_repository()
        batch_repo = container.import_batch_repository()
        
        # Parse batch ID
        try:
            batch_uuid = UUID(batch_id)
        except ValueError:
            console.print(f"[red]Invalid batch ID:[/red] {batch_id}")
            console.print("[dim]Batch ID must be a valid UUID[/dim]")
            raise typer.Exit(code=1)
        
        # Get batch info
        try:
            batch = batch_repo.get(batch_uuid)
        except Exception:
            console.print(f"[red]Batch not found:[/red] {batch_id}")
            raise typer.Exit(code=1)
        
        # Get entries
        entries = entry_repo.find_by_batch(batch_uuid)
        
        # Filter by status if provided
        if status:
            from finlite.domain.entities.statement_entry import StatementStatus
            try:
                status_filter = StatementStatus(status.upper())
                entries = [e for e in entries if e.status == status_filter]
            except ValueError:
                console.print(f"[red]Invalid status:[/red] {status}")
                console.print("[dim]Valid values: IMPORTED, MATCHED, POSTED[/dim]")
                raise typer.Exit(code=1)
        
        # Apply limit
        entries = entries[:limit]
        
        if not entries:
            console.print(f"[yellow]No entries found in batch {batch_id}[/yellow]")
            return
        
        # Show batch info
        console.print()
        console.print(Panel.fit(
            f"[bold]Batch:[/bold] {batch.id}\n"
            f"[bold]Source:[/bold] {batch.source.value}\n"
            f"[bold]Status:[/bold] {batch.status.value}\n"
            f"[bold]Total Entries:[/bold] {batch.transaction_count}\n"
            f"[bold]Filename:[/bold] {batch.filename or 'n/a'}",
            title="Import Batch Details",
            border_style="cyan",
        ))
        
        # Create entries table
        table = Table(
            title=f"Statement Entries ({len(entries)} shown)",
            show_header=True,
            header_style="bold cyan",
        )
        
        table.add_column("External ID", style="dim", width=20)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Payee", style="white", width=30)
        table.add_column("Amount", justify="right", style="green", width=15)
        table.add_column("Status", justify="center", width=10)
        
        for entry in entries:
            # Status color
            status_color = {
                "IMPORTED": "yellow",
                "MATCHED": "blue",
                "POSTED": "green",
            }.get(entry.status.value, "white")
            
            # Format amount with color (negative = red)
            amount_str = f"{entry.amount:,.2f} {entry.currency}"
            if entry.amount < 0:
                amount_str = f"[red]{amount_str}[/red]"
            else:
                amount_str = f"[green]{amount_str}[/green]"
            
            table.add_row(
                entry.external_id[:20],
                entry.occurred_at.strftime("%Y-%m-%d"),
                (entry.payee or entry.memo or "")[:30],
                amount_str,
                f"[{status_color}]{entry.status.value}[/{status_color}]",
            )
        
        console.print()
        console.print(table)
        console.print()
        console.print(f"[dim]Showing {len(entries)} entries[/dim]")
