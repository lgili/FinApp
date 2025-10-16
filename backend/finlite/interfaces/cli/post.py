"""
Post commands - Convert statement entries to balanced transactions.

Commands:
    fin post pending  - Post pending statement entries as transactions
"""

from typing import Annotated, Callable, Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from finlite.application.use_cases.post_pending_entries import (
    PostPendingEntriesUseCase,
    PostPendingEntriesCommand,
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
    Register post commands to the Typer app.

    Args:
        app: Typer app instance
        get_container: Function to get DI container
    """

    @app.command("pending")
    def post_pending(
        batch_id: Annotated[
            Optional[str],
            typer.Option("--batch", "-b", help="Post entries from specific batch ID"),
        ] = None,
        source_account: Annotated[
            str,
            typer.Option("--source", "-s", help="Source account code (e.g., Assets:Bank:Checking)"),
        ] = "Assets:Bank:Checking",
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run", "-d", help="Preview without saving changes"),
        ] = False,
        auto_post: Annotated[
            bool,
            typer.Option("--auto-post", "-a", help="Only post entries with suggested accounts"),
        ] = True,
    ):
        """
        Post pending statement entries as balanced transactions.

        Converts imported entries with suggested accounts into balanced
        double-entry transactions. Each entry creates a transaction with
        2 postings: source account and target account.

        Examples:
            $ fin post pending
            $ fin post pending --batch 123e4567-e89b-12d3-a456-426614174000
            $ fin post pending --source Assets:Bank:Nubank
            $ fin post pending --dry-run
            $ fin post pending --no-auto-post
        """
        container = get_container()
        use_case: PostPendingEntriesUseCase = container.post_pending_entries_use_case()

        console.print("[cyan]Posting pending entries...[/cyan]")

        try:
            # Parse batch ID if provided
            batch_uuid = None
            if batch_id:
                try:
                    batch_uuid = UUID(batch_id)
                except ValueError:
                    console.print(f"[red]Invalid batch ID:[/red] {batch_id}")
                    console.print("[dim]Batch ID must be a valid UUID[/dim]")
                    raise typer.Exit(code=1)

            # Execute use case
            command = PostPendingEntriesCommand(
                batch_id=batch_uuid,
                source_account_code=source_account,
                dry_run=dry_run,
                auto_post=auto_post,
            )

            result = use_case.execute(command)

            # Show results
            console.print()

            if result.total_entries == 0:
                console.print("[yellow]No pending entries found.[/yellow]")
                console.print("[dim]Apply rules first with 'fin rules apply'[/dim]")
                return

            # Summary panel
            post_rate = (result.posted_count / result.total_entries * 100) if result.total_entries > 0 else 0

            panel_text = (
                f"[bold]Total Entries:[/bold] {result.total_entries}\n"
                f"[bold]Posted:[/bold] [green]{result.posted_count}[/green] ({post_rate:.1f}%)\n"
                f"[bold]Skipped:[/bold] [yellow]{result.skipped_count}[/yellow]\n"
            )

            if result.error_count > 0:
                panel_text += f"[bold]Errors:[/bold] [red]{result.error_count}[/red]\n"

            if dry_run:
                panel_text += "\n[yellow]⚠ DRY RUN - No changes were saved[/yellow]"

            console.print(Panel.fit(
                panel_text,
                title="✓ Entries Posted" if not dry_run else "✓ Posting Preview",
                border_style="green" if not dry_run and result.error_count == 0 else "yellow",
            ))

            # Show posted entries table
            if result.posted_entries:
                table = Table(
                    title=f"Posted Transactions ({len(result.posted_entries)} entries)",
                    show_header=True,
                    header_style="bold cyan",
                )

                table.add_column("External ID", style="dim", width=20)
                table.add_column("Description", style="white", width=30)
                table.add_column("Amount", justify="right", width=15)
                table.add_column("Source → Target", style="cyan", width=40)

                # Show first 20 posted entries
                for posted in result.posted_entries[:20]:
                    # Format amount
                    amount_str = f"{posted.amount:,.2f} {posted.currency}"
                    if posted.amount < 0:
                        amount_str = f"[red]{amount_str}[/red]"
                    else:
                        amount_str = f"[green]+{amount_str}[/green]"

                    # Format account flow
                    flow = f"{posted.source_account} → {posted.target_account}"

                    table.add_row(
                        posted.external_id[:20],
                        posted.description[:30],
                        amount_str,
                        flow[:40],
                    )

                console.print()
                console.print(table)

                if len(result.posted_entries) > 20:
                    console.print(f"[dim]... and {len(result.posted_entries) - 20} more entries[/dim]")

            # Show errors if any
            if result.errors:
                console.print()
                console.print("[red bold]Errors:[/red bold]")
                for entry_id, error in result.errors[:5]:
                    console.print(f"  [red]•[/red] {entry_id}: {error}")

                if len(result.errors) > 5:
                    console.print(f"[dim]... and {len(result.errors) - 5} more errors[/dim]")

            # Next steps
            console.print()
            if not dry_run and result.posted_count > 0:
                console.print("[dim]Next steps:[/dim]")
                console.print("  • View transactions: [cyan]fin transactions list[/cyan]")
                console.print("  • Generate reports: [cyan]fin report cashflow[/cyan]")
            elif dry_run:
                console.print("[dim]Run without --dry-run to save changes[/dim]")
            elif result.skipped_count > 0:
                console.print("[dim]Tip: Review skipped entries and assign accounts manually[/dim]")

        except ValueError as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            if "Source account not found" in str(e):
                console.print(f"[dim]Create the account first: fin accounts create --code {source_account}[/dim]")
            raise typer.Exit(code=1)

        except Exception as e:
            console.print(f"[red]✗ Failed to post entries:[/red] {e}")
            logger.error("post_pending_failed", error=str(e), exc_info=True)
            raise typer.Exit(code=1)
