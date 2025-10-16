"""
Card commands - Credit card management.

Commands:
    fin card statement  - Generate credit card statement
    fin card pay        - Pay credit card invoice
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Callable, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from finlite.application.use_cases.build_card_statement import (
    BuildCardStatementCommand,
    BuildCardStatementUseCase,
)
from finlite.application.use_cases.pay_card import (
    PayCardCommand,
    PayCardUseCase,
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
    Register card commands to the Typer app.

    Args:
        app: Typer app instance
        get_container: Function to get DI container
    """

    @app.command("statement")
    def build_statement(
        card_account: Annotated[
            str,
            typer.Option("--card", "-c", help="Credit card account code (e.g., Liabilities:CreditCard:Nubank)"),
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
            typer.Option("--currency", help="Currency (BRL, USD, etc)"),
        ] = "BRL",
    ):
        """
        Generate credit card statement for a period.

        Shows all charges (purchases) made with the credit card,
        organized by date and category. Useful for reviewing
        expenses before paying the invoice.

        Examples:
            $ fin card statement --card Liabilities:CreditCard:Nubank
            $ fin card statement -c Liabilities:CreditCard:Nubank --from 2025-10-01 --to 2025-10-31
            $ fin card statement -c Liabilities:CreditCard:Nubank --currency USD
        """
        container = get_container()
        use_case: BuildCardStatementUseCase = container.build_card_statement_use_case()

        # Parse dates
        try:
            from_dt = (
                datetime.strptime(from_date, "%Y-%m-%d")
                if from_date
                else datetime(2000, 1, 1)
            )
            to_dt = (
                datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime.now()
            )
        except ValueError as e:
            console.print(f"[red]Invalid date format:[/red] {e}")
            console.print("[dim]Use YYYY-MM-DD format (e.g., 2025-10-01)[/dim]")
            raise typer.Exit(code=1)

        console.print(f"[cyan]Generating credit card statement...[/cyan]")
        console.print(f"[dim]Card: {card_account}[/dim]")
        console.print(f"[dim]Period: {from_dt.date()} to {to_dt.date()}[/dim]")

        try:
            # Execute use case
            command = BuildCardStatementCommand(
                card_account_code=card_account,
                from_date=from_dt,
                to_date=to_dt,
                currency=currency.upper(),
            )

            result = use_case.execute(command)

            # Show summary
            console.print()
            console.print(
                Panel.fit(
                    f"[bold]Card:[/bold] {result.card_account_name}\n"
                    f"[bold]Account:[/bold] {result.card_account_code}\n"
                    f"[bold]Period:[/bold] {result.from_date.date()} to {result.to_date.date()}\n"
                    f"[bold]Currency:[/bold] {result.currency}\n\n"
                    f"[bold]Previous Balance:[/bold] {result.previous_balance:,.2f} {result.currency}\n"
                    f"[bold]New Charges:[/bold] [red]{result.total_amount:,.2f}[/red] {result.currency}\n"
                    f"[bold]Total Purchases:[/bold] {result.item_count} transactions\n\n"
                    f"[bold]TOTAL TO PAY:[/bold] [bold red]{result.previous_balance + result.total_amount:,.2f}[/bold red] {result.currency}",
                    title="Credit Card Statement",
                    border_style="red",
                )
            )

            # Items table
            if result.items:
                console.print()
                items_table = Table(
                    title=f"Charges ({result.item_count} transactions)",
                    show_header=True,
                    header_style="bold red",
                )

                items_table.add_column("Date", style="cyan", width=12)
                items_table.add_column("Description", style="white", width=40)
                items_table.add_column(
                    "Amount", justify="right", style="red", width=15
                )
                items_table.add_column("Category", style="dim", width=30)

                for item in result.items:
                    items_table.add_row(
                        str(item.date),
                        item.description,
                        f"{item.amount:,.2f}",
                        item.category_code,
                    )

                # Add total row
                items_table.add_section()
                items_table.add_row(
                    "",
                    "[bold]TOTAL",
                    f"[bold red]{result.total_amount:,.2f}",
                    "",
                )

                console.print(items_table)
            else:
                console.print()
                console.print(
                    "[yellow]No charges found in this period.[/yellow]"
                )
                console.print(
                    "[dim]The card has no purchases in the specified date range[/dim]"
                )

            console.print()
            console.print("[green]✓ Statement generated successfully[/green]")

        except ValueError as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error("build_statement_failed", error=str(e))
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]✗ Failed to generate statement:[/red] {e}")
            logger.error("build_statement_failed", error=str(e), exc_info=True)
            raise typer.Exit(code=1)

    @app.command("pay")
    def pay_invoice(
        card_account: Annotated[
            str,
            typer.Option(
                "--card",
                "-c",
                help="Credit card account code (e.g., Liabilities:CreditCard:Nubank)",
            ),
        ],
        payment_account: Annotated[
            str,
            typer.Option(
                "--from",
                "-f",
                help="Payment source account (e.g., Assets:Checking)",
            ),
        ],
        amount: Annotated[
            float,
            typer.Option("--amount", "-a", help="Payment amount"),
        ],
        currency: Annotated[
            str,
            typer.Option("--currency", help="Currency (BRL, USD, etc)"),
        ] = "BRL",
        date: Annotated[
            Optional[str],
            typer.Option("--date", "-d", help="Payment date (YYYY-MM-DD, default: today)"),
        ] = None,
        description: Annotated[
            str,
            typer.Option(
                "--description", help="Payment description"
            ),
        ] = "Credit card payment",
    ):
        """
        Pay credit card invoice.

        Creates a transaction that transfers money from a bank account (ASSET)
        to the credit card (LIABILITY), reducing the debt.

        Examples:
            $ fin card pay -c Liabilities:CreditCard:Nubank -f Assets:Checking -a 1500.00
            $ fin card pay -c Liabilities:CreditCard:Nubank -f Assets:Checking -a 2500.00 --date 2025-10-15
            $ fin card pay -c Liabilities:CreditCard:Nubank -f Assets:Checking -a 1000.00 --description "Partial payment"
        """
        container = get_container()
        use_case: PayCardUseCase = container.pay_card_use_case()

        # Parse date
        try:
            payment_date = (
                datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
            )
        except ValueError as e:
            console.print(f"[red]Invalid date format:[/red] {e}")
            console.print("[dim]Use YYYY-MM-DD format (e.g., 2025-10-15)[/dim]")
            raise typer.Exit(code=1)

        # Validate amount
        if amount <= 0:
            console.print("[red]Payment amount must be positive[/red]")
            raise typer.Exit(code=1)

        console.print(f"[cyan]Processing credit card payment...[/cyan]")
        console.print(f"[dim]Card: {card_account}[/dim]")
        console.print(f"[dim]From: {payment_account}[/dim]")
        console.print(f"[dim]Amount: {amount:,.2f} {currency}[/dim]")
        console.print(f"[dim]Date: {payment_date.date()}[/dim]")

        try:
            # Execute use case
            command = PayCardCommand(
                card_account_code=card_account,
                payment_account_code=payment_account,
                amount=Decimal(str(amount)),
                currency=currency.upper(),
                date=payment_date,
                description=description,
            )

            result = use_case.execute(command)

            # Show success
            console.print()
            console.print(
                Panel.fit(
                    f"[bold]Payment Successful[/bold]\n\n"
                    f"[bold]Transaction ID:[/bold] {result.transaction_id}\n"
                    f"[bold]Card:[/bold] {result.card_account_code}\n"
                    f"[bold]From:[/bold] {result.payment_account_code}\n"
                    f"[bold]Amount:[/bold] [green]{result.amount:,.2f}[/green] {result.currency}\n"
                    f"[bold]Date:[/bold] {result.date.date()}\n\n"
                    f"[dim]The payment has been recorded and the card balance has been updated.[/dim]",
                    title="Payment Confirmation",
                    border_style="green",
                )
            )

            console.print()
            console.print("[green]✓ Payment processed successfully[/green]")

        except ValueError as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error("pay_card_failed", error=str(e))
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]✗ Failed to process payment:[/red] {e}")
            logger.error("pay_card_failed", error=str(e), exc_info=True)
            raise typer.Exit(code=1)
