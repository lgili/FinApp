"""Transaction commands using Use Cases."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Callable

import typer
from rich.console import Console
from rich.table import Table

from finlite.application.dtos import CreateTransactionDTO, CreatePostingDTO, TransactionFilterDTO

console = Console()


def register_commands(app: typer.Typer, get_container: Callable):
    """Register transaction commands to the Typer app."""
    
    @app.command("create")
    def create_transaction(
        description: Annotated[str, typer.Option("--description", "-d", help="Transaction description")],
        date: Annotated[
            str | None,
            typer.Option("--date", help="Transaction date (YYYY-MM-DD). Defaults to today"),
        ] = None,
        payee: Annotated[
            str | None, typer.Option("--payee", "-p", help="Payee/vendor name")
        ] = None,
    ):
        """
        Create a new transaction (interactive mode for postings).
        
        A transaction requires at least 2 postings (double-entry).
        You'll be prompted to enter postings interactively.
        
        Examples:
            $ fin transactions create -d "Salary payment"
            $ fin transactions create -d "Grocery shopping" --payee "Walmart"
            $ fin transactions create -d "Rent" --date 2025-01-01
        """
        try:
            # Parse date
            txn_date = datetime.fromisoformat(date) if date else datetime.now()
            
            console.print(f"\n[bold]Creating transaction: {description}[/bold]")
            console.print(f"Date: {txn_date.date()}")
            if payee:
                console.print(f"Payee: {payee}")
            
            # Collect postings interactively
            postings: list[CreatePostingDTO] = []
            console.print("\n[cyan]Enter postings (minimum 2 required)[/cyan]")
            console.print("[dim]Press Enter on empty account to finish[/dim]\n")
            
            while True:
                posting_num = len(postings) + 1
                
                # Get account
                account_code = console.input(f"Posting {posting_num} - Account code: ").strip()
                if not account_code:
                    if len(postings) < 2:
                        console.print("[yellow]At least 2 postings required![/yellow]")
                        continue
                    break
                
                # Get amount
                amount_str = console.input(f"Posting {posting_num} - Amount (negative for credit): ").strip()
                try:
                    amount = Decimal(amount_str)
                except Exception:
                    console.print("[red]Invalid amount! Try again.[/red]")
                    continue
                
                postings.append(
                    CreatePostingDTO(
                        account_code=account_code,
                        amount=amount,
                        currency="USD",  # TODO: Get from account or allow input
                    )
                )
                
                console.print(f"[green]✓ Posting {posting_num} added[/green]\n")
            
            # Validate balance
            total = sum(p.amount for p in postings)
            if total != 0:
                console.print(f"[red]❌ Transaction doesn't balance! Total: {total}[/red]")
                console.print("[yellow]The sum of all postings must equal zero.[/yellow]")
                raise typer.Exit(1)
            
            # Get container and use case
            container = get_container()
            use_case = container.record_transaction_use_case()
            
            # Create DTO
            dto = CreateTransactionDTO(
                description=description,
                date=txn_date,
                payee=payee,
                postings=postings,
            )
            
            # Execute use case
            result = use_case.execute(dto)
            
            # Display result
            console.print(f"\n✅ [green]Transaction created successfully![/green]")
            console.print(f"   ID: {result.transaction.id}")
            console.print(f"   Description: {result.transaction.description}")
            console.print(f"   Date: {result.transaction.date.date()}")
            console.print(f"   Postings: {len(result.transaction.postings)}")
            
        except ValueError as e:
            console.print(f"❌ [red]Invalid input: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"❌ [red]Unexpected error: {e}[/red]")
            raise typer.Exit(1)

    @app.command("list")
    def list_transactions(
        account: Annotated[
            str | None, typer.Option("--account", "-a", help="Filter by account code")
        ] = None,
        start_date: Annotated[
            str | None, typer.Option("--start", help="Start date (YYYY-MM-DD)")
        ] = None,
        end_date: Annotated[
            str | None, typer.Option("--end", help="End date (YYYY-MM-DD)")
        ] = None,
        limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum results")] = 20,
    ):
        """
        List transactions with optional filters.
        
        Examples:
            $ fin transactions list
            $ fin transactions list --account CASH001
            $ fin transactions list --start 2025-01-01 --end 2025-12-31
            $ fin transactions list -a BANK001 --limit 50
        """
        try:
            # Parse dates
            start = datetime.fromisoformat(start_date) if start_date else None
            end = datetime.fromisoformat(end_date) if end_date else None
            
            # Get container and use case
            container = get_container()
            use_case = container.list_transactions_use_case()
            
            # Create filter DTO
            filters = TransactionFilterDTO(
                account_code=account,
                start_date=start,
                end_date=end,
                limit=limit,
            )
            
            # Execute use case
            transactions = use_case.execute(filters)
            
            # Display results
            if not transactions:
                console.print("[yellow]No transactions found[/yellow]")
                return
            
            # Create table
            table = Table(title=f"Transactions ({len(transactions)} results)")
            table.add_column("Date", style="cyan")
            table.add_column("Description", style="white", no_wrap=False)
            table.add_column("Payee", style="yellow")
            table.add_column("Postings", style="magenta", justify="right")
            
            for txn in transactions:
                table.add_row(
                    txn.date.strftime("%Y-%m-%d"),
                    txn.description,
                    txn.payee or "-",
                    str(len(txn.postings)),
                )
            
            console.print(table)
            
            # Show posting details if requested
            show_details = typer.confirm("\nShow posting details?", default=False)
            if show_details:
                console.print()
                for txn in transactions:
                    console.print(f"[bold]{txn.date.strftime('%Y-%m-%d')} - {txn.description}[/bold]")
                    for posting in txn.postings:
                        sign = "+" if posting.amount >= 0 else ""
                        console.print(
                            f"  {posting.account_code:20} {sign}{posting.amount:>12} {posting.currency}"
                        )
                        if posting.memo:
                            console.print(f"    [dim]{posting.memo}[/dim]")
                    console.print()
            
        except ValueError as e:
            console.print(f"❌ [red]Invalid input: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"❌ [red]Unexpected error: {e}[/red]")
            raise typer.Exit(1)
