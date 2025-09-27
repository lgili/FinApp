"""Typer CLI entrypoint for finlite."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from finlite.config import Settings, get_settings
from finlite.core.accounts import (
    AccountCreate,
    AccountType,
    create_account,
    list_accounts,
    seed_default_chart,
)
from finlite.db.migrator import upgrade_head
from finlite.db.session import session_scope
from finlite.logging import get_logger

console = Console()
get_logger(__name__)

app = typer.Typer(help="Finlite CLI — local-first double-entry accounting")
accounts_app = typer.Typer(help="Account management commands")
app.add_typer(accounts_app, name="accounts")


def _resolve_settings() -> Settings:
    return get_settings()


@app.command("init-db")
def init_db(seed: bool = typer.Option(True, help="Seed default chart of accounts")) -> None:
    """Create the SQLite database and apply migrations."""
    settings = _resolve_settings()
    console.print(f"[bold green]Applying migrations at[/bold green] {settings.database_path}")
    upgrade_head(settings)
    if seed:
        with session_scope(settings) as session:
            seed_default_chart(session)
        console.print("Default chart of accounts ensured.")
    console.print("Database ready.")


@accounts_app.command("seed")
def seed_accounts() -> None:
    """Ensure the default chart of accounts is present."""
    settings = _resolve_settings()
    with session_scope(settings) as session:
        seed_default_chart(session)
    console.print("Default chart ensured.")


@accounts_app.command("list")
def list_accounts_cmd() -> None:
    """List accounts ordered by name."""
    settings = _resolve_settings()
    with session_scope(settings) as session:
        accounts = list_accounts(session)
    table = Table(title="Accounts")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Currency")
    table.add_column("Code")
    for account in accounts:
        table.add_row(
            str(account.id), account.name, account.type.value, account.currency, account.code or ""
        )
    console.print(table)


@accounts_app.command("add")
def add_account(
    name: str = typer.Argument(..., help="Account name"),
    type_: AccountType = typer.Option(..., "--type", help="Account type"),
    currency: str = typer.Option("BRL", help="Account currency"),
    code: str | None = typer.Option(None, help="Optional account code"),
    parent_id: int | None = typer.Option(None, help="Parent account ID"),
) -> None:
    """Create a new account."""
    payload = AccountCreate(
        name=name, type=type_, currency=currency, code=code, parent_id=parent_id
    )
    settings = _resolve_settings()
    with session_scope(settings) as session:
        account = create_account(session, payload)
        console.print(f"Created account [bold]{account.name}[/bold] (id={account.id}).")


@app.command("config")
def show_config() -> None:
    """Display effective configuration values."""
    settings = _resolve_settings()
    table = Table(title="Configuration")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("data_dir", str(settings.data_dir))
    table.add_row("database_path", str(settings.database_path))
    table.add_row("locale", settings.locale)
    table.add_row("default_currency", settings.default_currency)
    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
