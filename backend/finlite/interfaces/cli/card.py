"""CLI commands for credit card management."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Callable, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from finlite.application.use_cases.build_card_statement import (
    BuildCardStatementCommand,
    BuildCardStatementUseCase,
    CardStatementResult,
)
from finlite.application.use_cases.list_accounts import ListAccountsUseCase
from finlite.application.use_cases.pay_card import PayCardCommand, PayCardUseCase
from finlite.domain.value_objects.account_type import AccountType
from finlite.shared.di import Container
from finlite.shared.observability import get_logger

logger = get_logger(__name__)
console = Console()


def register_commands(app: typer.Typer, get_container: Callable[[], Container]) -> None:
    """Register Typer commands for credit card flows."""

    @app.command("list")
    def list_cards() -> None:
        """List all configured credit card accounts and their metadata."""

        container = get_container()
        use_case: ListAccountsUseCase = container.list_accounts_use_case()
        accounts = use_case.execute(account_type=AccountType.LIABILITY)
        card_accounts = [acc for acc in accounts if acc.card_issuer]

        if not card_accounts:
            console.print("[yellow]No credit card accounts configured yet.[/yellow]")
            console.print(
                "[dim]Create one with --card-issuer, --card-closing-day, and --card-due-day.[/dim]"
            )
            return

        table = Table(title=f"Credit Cards ({len(card_accounts)} accounts)")
        table.add_column("Code", style="cyan")
        table.add_column("Issuer", style="magenta")
        table.add_column("Closing Day", justify="right")
        table.add_column("Due Day", justify="right")

        for acc in card_accounts:
            table.add_row(
                acc.code,
                acc.card_issuer or "-",
                str(acc.card_closing_day or "-"),
                str(acc.card_due_day or "-"),
            )

        console.print(table)

    def _run_build_statement(
        container: Container,
        card_account: str,
        period: str | None,
        currency: str,
        show_items: bool,
    ) -> None:
        period_date = _parse_period(period)
        use_case: BuildCardStatementUseCase = container.build_card_statement_use_case()
        command = BuildCardStatementCommand(
            card_account_code=card_account,
            period=period_date,
            currency=currency.upper(),
        )
        result = use_case.execute(command)
        _render_statement(result, show_items)

    @app.command("build-statement")
    def build_statement(
        card_account: Annotated[
            str,
            typer.Option("--card", "-c", help="Credit card account code"),
        ],
        period: Annotated[
            Optional[str],
            typer.Option("--period", "-p", help="Statement period (YYYY-MM)"),
        ] = None,
        currency: Annotated[
            str,
            typer.Option("--currency", help="Currency filter"),
        ] = "BRL",
        show_items: Annotated[
            bool,
            typer.Option("--show-items/--no-show-items", help="Toggle charges table"),
        ] = True,
    ) -> None:
        """Generate and persist a credit card statement for the target period."""

        container = get_container()
        try:
            _run_build_statement(container, card_account, period, currency, show_items)
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1)

    @app.command("statement")
    def deprecated_statement(**kwargs) -> None:  # pragma: no cover - compatibility wrapper
        console.print("[yellow]`fin card statement` is deprecated. Use `fin card build-statement`.[/yellow]")
        build_statement(**kwargs)

    @app.command("pay")
    def pay_statement(
        card_account: Annotated[
            str,
            typer.Option("--card", "-c", help="Credit card account code"),
        ],
        payment_account: Annotated[
            str,
            typer.Option("--from", "-f", help="Funding account code"),
        ],
        amount: Annotated[
            float,
            typer.Option("--amount", "-a", help="Payment amount"),
        ],
        currency: Annotated[
            str,
            typer.Option("--currency", help="Currency"),
        ] = "BRL",
        payment_date: Annotated[
            Optional[str],
            typer.Option("--date", help="Payment date (YYYY-MM-DD)"),
        ] = None,
        description: Annotated[
            Optional[str],
            typer.Option("--description", help="Payment description"),
        ] = None,
    ) -> None:
        """Register a credit card payment."""

        try:
            when = datetime.strptime(payment_date, "%Y-%m-%d") if payment_date else datetime.now()
        except ValueError as exc:
            console.print(f"[red]Invalid date:[/red] {exc}")
            raise typer.Exit(1)

        container = get_container()
        use_case: PayCardUseCase = container.pay_card_use_case()

        command = PayCardCommand(
            card_account_code=card_account,
            payment_account_code=payment_account,
            amount=Decimal(str(amount)),
            currency=currency.upper(),
            date=when,
            description=description or "Credit card payment",
        )

        try:
            result = use_case.execute(command)
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1)

        console.print(
            Panel.fit(
                f"[bold]Payment recorded[/bold]\n"
                f"Card: {result.card_account_code}\n"
                f"From: {result.payment_account_code}\n"
                f"Amount: {result.amount:,.2f} {result.currency}\n"
                f"Date: {result.date.strftime('%Y-%m-%d')}\n",
                border_style="green",
            )
        )

    def _parse_period(period: Optional[str]) -> date:
        if period is None:
            today = datetime.now().date()
            return today.replace(day=1)
        try:
            parsed = datetime.strptime(period, "%Y-%m")
        except ValueError as exc:  # pragma: no cover - guard
            raise ValueError(f"Invalid period '{period}': {exc}")
        return parsed.date().replace(day=1)

    def _render_statement(result: CardStatementResult, show_items: bool) -> None:
        console.print(
            Panel.fit(
                f"[bold]Card:[/bold] {result.card_account_name}\n"
                f"[bold]Account Code:[/bold] {result.card_account_code}\n"
                f"[bold]Period:[/bold] {result.period_start:%Y-%m-%d} → {result.period_end:%Y-%m-%d}\n"
                f"[bold]Closing Day:[/bold] {result.closing_day}\n"
                f"[bold]Due Date:[/bold] {result.due_date:%Y-%m-%d}\n"
                f"[bold]Status:[/bold] {result.status.value}\n\n"
                f"[bold]Previous Balance:[/bold] {result.previous_balance:,.2f} {result.currency}\n"
                f"[bold]New Charges:[/bold] {result.charges_total:,.2f} {result.currency}\n"
                f"[bold red]Total Due:[/bold red] {result.total_due:,.2f} {result.currency}",
                title="Credit Card Statement",
                border_style="red",
            )
        )

        if not show_items:
            console.print("[dim]Use --show-items to list individual charges.[/dim]")
            return

        if not result.items:
            console.print("[yellow]No purchases for this period.[/yellow]")
            return

        table = Table(title=f"Charges ({len(result.items)} items)")
        table.add_column("Date", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Amount", justify="right", style="red")
        table.add_column("Category", style="dim")
        table.add_column("Installment", style="magenta")

        for item in result.items:
            if item.installment_number and item.installment_total:
                installment_label = f"{item.installment_number}/{item.installment_total}"
            else:
                installment_label = "-"
            table.add_row(
                item.occurred_at.strftime("%Y-%m-%d"),
                item.description,
                f"{item.amount:,.2f}",
                item.category_code,
                installment_label,
            )

        console.print(table)
