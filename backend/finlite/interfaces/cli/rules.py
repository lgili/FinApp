"""
Rules commands - Apply classification rules to imported entries.

Commands:
    fin rules apply  - Apply classification rules to imported entries
"""

from typing import Annotated, Callable, Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from finlite.application.use_cases.apply_rules import (
    ApplyRulesUseCase,
    ApplyRulesCommand,
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
    Register rules commands to the Typer app.

    Args:
        app: Typer app instance
        get_container: Function to get DI container
    """

    @app.command("apply")
    def apply_rules(
        batch_id: Annotated[
            Optional[str],
            typer.Option("--batch", "-b", help="Apply rules to specific batch ID"),
        ] = None,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run", "-d", help="Preview without saving changes"),
        ] = False,
        auto_apply: Annotated[
            bool,
            typer.Option("--auto-apply", "-a", help="Automatically apply high-confidence matches"),
        ] = True,
    ):
        """
        Apply classification rules to imported statement entries.

        Rules are loaded from rules.json and matched against imported entries.
        Matched entries will have a suggested account assigned.

        Examples:
            $ fin rules apply
            $ fin rules apply --batch 123e4567-e89b-12d3-a456-426614174000
            $ fin rules apply --dry-run
            $ fin rules apply --no-auto-apply
        """
        container = get_container()
        use_case: ApplyRulesUseCase = container.apply_rules_use_case()

        console.print("[cyan]Applying classification rules...[/cyan]")

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
            command = ApplyRulesCommand(
                batch_id=batch_uuid,
                dry_run=dry_run,
                auto_apply=auto_apply,
            )

            result = use_case.execute(command)

            # Show results
            console.print()

            if result.total_entries == 0:
                console.print("[yellow]No imported entries found.[/yellow]")
                console.print("[dim]Import a statement first with 'fin import nubank <file>'[/dim]")
                return

            # Summary panel
            match_rate = (result.matched_entries / result.total_entries * 100) if result.total_entries > 0 else 0

            panel_text = (
                f"[bold]Total Entries:[/bold] {result.total_entries}\n"
                f"[bold]Matched:[/bold] [green]{result.matched_entries}[/green] ({match_rate:.1f}%)\n"
                f"[bold]Unmatched:[/bold] [yellow]{result.unmatched_entries}[/yellow]\n"
            )

            if dry_run:
                panel_text += "\n[yellow]⚠ DRY RUN - No changes were saved[/yellow]"

            console.print(Panel.fit(
                panel_text,
                title="✓ Rules Applied" if not dry_run else "✓ Rules Preview",
                border_style="green" if not dry_run else "yellow",
            ))

            # Show matched entries table
            if result.applications:
                table = Table(
                    title=f"Rule Matches ({len(result.applications)} entries)",
                    show_header=True,
                    header_style="bold cyan",
                )

                table.add_column("External ID", style="dim", width=20)
                table.add_column("Memo", style="white", width=35)
                table.add_column("Amount", justify="right", width=15)
                table.add_column("Suggested Account", style="cyan", width=30)
                table.add_column("Confidence", justify="center", width=12)

                # Show first 20 applications
                for app in result.applications[:20]:
                    # Confidence color
                    confidence_color = {
                        "high": "green",
                        "medium": "yellow",
                        "low": "red",
                        "none": "dim",
                    }.get(app.confidence, "white")

                    # Format amount
                    amount_str = f"{app.amount:,.2f}"
                    if app.amount < 0:
                        amount_str = f"[red]{amount_str}[/red]"
                    else:
                        amount_str = f"[green]+{amount_str}[/green]"

                    table.add_row(
                        app.entry_external_id[:20],
                        (app.entry_memo or "")[:35],
                        amount_str,
                        app.suggested_account_code or "[dim]no match[/dim]",
                        f"[{confidence_color}]{app.confidence}[/{confidence_color}]",
                    )

                console.print()
                console.print(table)

                if len(result.applications) > 20:
                    console.print(f"[dim]... and {len(result.applications) - 20} more entries[/dim]")

            # Next steps
            console.print()
            if not dry_run and result.matched_entries > 0:
                console.print("[dim]Next steps:[/dim]")
                console.print("  • Post matched entries: [cyan]fin post pending[/cyan]")
                console.print("  • Review entries: [cyan]fin import entries <batch-id>[/cyan]")
            elif dry_run:
                console.print("[dim]Run without --dry-run to save changes[/dim]")

        except FileNotFoundError as e:
            console.print(f"[red]✗ Rules file not found:[/red] {e}")
            console.print("[dim]Create a rules.json file in your data directory[/dim]")
            raise typer.Exit(code=1)

        except Exception as e:
            console.print(f"[red]✗ Failed to apply rules:[/red] {e}")
            logger.error("apply_rules_failed", error=str(e), exc_info=True)
            raise typer.Exit(code=1)
