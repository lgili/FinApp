"""Account management commands using Use Cases."""

from typing import Annotated, Callable

import typer
from rich.console import Console
from rich.table import Table

from finlite.application.dtos import CreateAccountDTO
from finlite.application.exceptions import AccountAlreadyExistsError

console = Console()


def register_commands(app: typer.Typer, get_container: Callable):
    """Register account commands to the Typer app."""
    
    @app.command("create")
    def create_account(
        code: Annotated[str, typer.Option("--code", "-c", help="Unique account code")],
        name: Annotated[str, typer.Option("--name", "-n", help="Account display name")],
        account_type: Annotated[
            str,
            typer.Option(
                "--type",
                "-t",
                help="Account type: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE",
            ),
        ],
        currency: Annotated[
            str, typer.Option("--currency", help="Currency code (e.g., USD, BRL)")
        ] = "USD",
        parent_code: Annotated[
            str | None, typer.Option("--parent", help="Parent account code (optional)")
        ] = None,
    ):
        """
        Create a new account.
        
        Examples:
            $ fin accounts create --code "CASH001" --name "Cash" --type ASSET --currency USD
            $ fin accounts create -c "BANK001" -n "Checking Account" -t ASSET
            $ fin accounts create -c "EXPENSE001" -n "Groceries" -t EXPENSE --parent "EXPENSE"
        """
        try:
            # Get container and use case
            container = get_container()
            use_case = container.create_account_use_case()
            
            # Create DTO
            dto = CreateAccountDTO(
                code=code,
                name=name,
                type=account_type.upper(),
                currency=currency.upper(),
                parent_code=parent_code,
            )
            
            # Execute use case
            result = use_case.execute(dto)
            
            # Display result
            if result.created:
                console.print(f"✅ [green]Account created successfully![/green]")
                console.print(f"   Code: [bold]{result.account.code}[/bold]")
                console.print(f"   Name: {result.account.name}")
                console.print(f"   Type: {result.account.type}")
                console.print(f"   Currency: {result.account.currency}")
            else:
                console.print(f"ℹ️  [yellow]Account already exists[/yellow]")
                
        except AccountAlreadyExistsError as e:
            console.print(f"❌ [red]Error: {e}[/red]")
            raise typer.Exit(1)
        except ValueError as e:
            console.print(f"❌ [red]Invalid input: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"❌ [red]Unexpected error: {e}[/red]")
            raise typer.Exit(1)

    @app.command("list")
    def list_accounts(
        account_type: Annotated[
            str | None,
            typer.Option(
                "--type", "-t", help="Filter by type: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE"
            ),
        ] = None,
    ):
        """
        List all accounts.
        
        Examples:
            $ fin accounts list
            $ fin accounts list --type ASSET
            $ fin accounts list -t EXPENSE
        """
        try:
            # Get container and use case
            container = get_container()
            use_case = container.list_accounts_use_case()
            
            # Execute use case
            accounts = use_case.execute(
                account_type=account_type.upper() if account_type else None
            )
            
            # Display results
            if not accounts:
                console.print("[yellow]No accounts found[/yellow]")
                return
            
            # Create table
            table = Table(title=f"Accounts ({len(accounts)} total)")
            table.add_column("Code", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Type", style="magenta")
            table.add_column("Currency", style="green")
            
            for account in accounts:
                table.add_row(
                    account.code,
                    account.name,
                    account.type,
                    account.currency,
                )
            
            console.print(table)
            
        except ValueError as e:
            console.print(f"❌ [red]Invalid input: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"❌ [red]Unexpected error: {e}[/red]")
            raise typer.Exit(1)

    @app.command("balance")
    def get_balance(
        code: Annotated[str, typer.Argument(help="Account code")],
    ):
        """
        Get account balance.
        
        Examples:
            $ fin accounts balance CASH001
            $ fin accounts balance BANK001
        """
        try:
            # Get container and use case
            container = get_container()
            use_case = container.get_account_balance_use_case()
            
            # Execute use case
            result = use_case.execute_by_code(code)
            
            # Display result
            console.print(f"\n[bold]Account: {result.name}[/bold]")
            console.print(f"Code: {result.code}")
            console.print(f"Type: {result.type}")
            console.print(f"Currency: {result.currency}")
            console.print(f"\n[bold cyan]Balance: {result.balance} {result.currency}[/bold cyan]")
            console.print("[dim]No transactions yet[/dim]")
            
        except ValueError as e:
            console.print(f"❌ [red]{e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"❌ [red]Unexpected error: {e}[/red]")
            raise typer.Exit(1)
