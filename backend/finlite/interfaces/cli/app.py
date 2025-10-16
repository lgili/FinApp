"""
Modern CLI application using Typer + DI Container + Use Cases.

This is the new CLI implementation that follows Clean Architecture principles:
- Uses DI Container for dependency injection
- Delegates business logic to Use Cases
- No direct database access
- Testable and maintainable

Example usage:
    $ fin accounts create --code "CASH001" --name "Cash" --type ASSET --currency USD
    $ fin accounts list
    $ fin transactions create --description "Salary" ...
"""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from finlite.shared.di import Container, create_container, init_database
from finlite.shared.observability import setup_logging, get_logger

# Initialize logging and console
logger = get_logger(__name__)
console = Console()

# Create Typer app
app = typer.Typer(
    name="fin",
    help="Finlite - Local-first double-entry accounting with Clean Architecture",
    no_args_is_help=True,
)

# Sub-apps for organization
accounts_app = typer.Typer(help="Account management commands")
transactions_app = typer.Typer(help="Transaction commands")
import_app = typer.Typer(help="Import bank statements")
rules_app = typer.Typer(help="Apply classification rules")
post_app = typer.Typer(help="Post statement entries as transactions")
report_app = typer.Typer(help="Generate financial reports")
export_app = typer.Typer(help="Export data to various formats")

# Register sub-apps
app.add_typer(accounts_app, name="accounts")
app.add_typer(transactions_app, name="transactions")
app.add_typer(import_app, name="import")
app.add_typer(rules_app, name="rules")
app.add_typer(post_app, name="post")
app.add_typer(report_app, name="report")
app.add_typer(export_app, name="export")

# Global container instance (initialized on first command)
_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get or create the global DI container.
    
    Uses SQLite by default. Can be configured via environment variables.
    
    Returns:
        Initialized DI Container
    """
    global _container
    
    if _container is None:
        # TODO: Load from config file or environment
        database_url = "sqlite:///finlite.db"
        
        _container = create_container(database_url, echo=False)
        init_database(_container)
        
        console.print(f"[dim]Connected to: {database_url}[/dim]")
    
    return _container


# Import and register commands (must be after get_container definition)
from finlite.interfaces.cli import accounts as accounts_module  # noqa: E402
from finlite.interfaces.cli import transactions as transactions_module  # noqa: E402
from finlite.interfaces.cli import imports as imports_module  # noqa: E402
from finlite.interfaces.cli import rules as rules_module  # noqa: E402
from finlite.interfaces.cli import post as post_module  # noqa: E402
from finlite.interfaces.cli import reports as reports_module  # noqa: E402
from finlite.interfaces.cli import export as export_module  # noqa: E402

accounts_module.register_commands(accounts_app, get_container)
transactions_module.register_commands(transactions_app, get_container)
imports_module.register_commands(import_app, get_container)
rules_module.register_commands(rules_app, get_container)
post_module.register_commands(post_app, get_container)
reports_module.register_commands(report_app, get_container)
export_module.register_commands(export_app, get_container)


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", help="Show version and exit"),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
    json_logs: Annotated[
        bool,
        typer.Option("--json-logs", help="Output logs as JSON"),
    ] = False,
):
    """
    Finlite CLI - Local-first accounting toolkit.

    Commands:
        accounts     - Manage accounts
        transactions - Manage transactions
        import       - Import bank statements
        rules        - Apply classification rules
        post         - Post entries as transactions
        report       - Generate financial reports
        export       - Export data to various formats

    Global Options:
        --debug      - Enable debug logging
        --json-logs  - Output logs as JSON (useful for log aggregation)
    """
    # Setup logging based on options
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(debug=debug, json_output=json_logs, log_level=log_level)
    
    logger.debug("cli_started", command=ctx.invoked_subcommand)
    
    if version:
        console.print("finlite version 0.2.0")
        raise typer.Exit()


def main():
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
