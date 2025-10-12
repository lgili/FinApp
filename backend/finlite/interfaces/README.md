# Interfaces Layer

Esta camada contém **adaptadores de entrada** (CLI, API, TUI) que expõem o sistema para usuários.

## Princípios

- ✅ **Thin adapters** - apenas parse input + call use case + present output
- ✅ **Sem lógica de negócio** - delega tudo para `application/`
- ✅ **Presentation logic** - formatação, Rich tables, JSON, etc.
- ✅ **Dependency Injection** - resolve use cases via container

## Estrutura

```
interfaces/
├── cli/
│   ├── app.py                 # Typer entrypoint
│   ├── commands/
│   │   ├── accounts.py
│   │   ├── transactions.py
│   │   ├── import.py
│   │   ├── post.py
│   │   ├── rules.py
│   │   ├── reports.py
│   │   └── ask.py
│   │
│   └── presenters/
│       ├── account_presenter.py
│       ├── transaction_presenter.py
│       └── report_presenter.py
│
├── api/                       # (Fase 11) FastAPI
│   └── ...
│
└── tui/                       # (Fase 2B) Textual
    └── ...
```

## Exemplo: CLI Command (thin adapter)

```python
# interfaces/cli/commands/import.py
import typer
from pathlib import Path
from finlite.shared.di import get_container
from finlite.application.ingestion.import_nubank import ImportNubankCommand

import_app = typer.Typer()

@import_app.command("nubank")
def import_nubank_cmd(
    file_path: Path = typer.Argument(..., help="Path to Nubank CSV file"),
    account: str | None = typer.Option(None, "--account", help="Account hint"),
):
    """Import Nubank CSV file."""
    
    # 1. Obter container (DI)
    container = get_container()
    
    # 2. Construir comando (DTO)
    cmd = ImportNubankCommand(
        file_path=file_path,
        account_hint=account,
        default_currency=container.config().default_currency,
    )
    
    # 3. Chamar use case
    try:
        result = container.import_nubank_use_case()(cmd)
    except FileNotFoundError as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)
    except DuplicateImportError as e:
        typer.echo(f"⚠️  {e}", err=True)
        raise typer.Exit(0)
    
    # 4. Apresentar resultado (presenter)
    from finlite.interfaces.cli.presenters import ImportPresenter
    ImportPresenter.show_success(result)
```

## Exemplo: Presenter

```python
# interfaces/cli/presenters/import_presenter.py
from rich.console import Console
from rich.table import Table
from finlite.application.ingestion.import_nubank import ImportNubankResult

console = Console()

class ImportPresenter:
    @staticmethod
    def show_success(result: ImportNubankResult):
        console.print(f"✓ [green]Import completed[/green]")
        
        table = Table(show_header=False)
        table.add_row("Batch ID", str(result.batch_id))
        table.add_row("Entries", str(result.entries_count))
        table.add_row("Duplicates skipped", str(result.duplicates_skipped))
        
        console.print(table)
```

## CLI Principal (app.py)

```python
# interfaces/cli/app.py
import typer
from finlite.interfaces.cli.commands import (
    accounts,
    transactions,
    import_cmd,
    post,
    rules,
    reports,
    export_cmd,
    ask,
)

app = typer.Typer(help="Finlite CLI — local-first double-entry accounting")

# Registrar sub-comandos
app.add_typer(accounts.accounts_app, name="accounts")
app.add_typer(transactions.txn_app, name="txn")
app.add_typer(import_cmd.import_app, name="import")
app.add_typer(post.post_app, name="post")
app.add_typer(rules.rules_app, name="rules")
app.add_typer(reports.report_app, name="report")
app.add_typer(export_cmd.export_app, name="export")
app.add_typer(ask.ask_app, name="ask")

@app.command()
def init_db(seed: bool = True):
    """Initialize database and run migrations."""
    container = get_container()
    container.init_db_use_case()(seed=seed)
    typer.echo("✓ Database initialized")

def main():
    app()
```

## Dependency Injection

```python
# shared/di.py
from dependency_injector import containers, providers
from finlite.application.ingestion.import_nubank import import_nubank
from finlite.infrastructure.persistence.sqlalchemy import SqlAlchemyUnitOfWork

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_settings)
    
    session_factory = providers.Singleton(
        create_session_factory,
        config.provided.database_url,
    )
    
    uow = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)
    event_bus = providers.Singleton(InMemoryEventBus)
    
    # Use cases
    import_nubank_use_case = providers.Factory(
        import_nubank,
        uow=uow,
        event_bus=event_bus,
    )

_container = None

def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container
```

## Testes E2E

```python
# tests/e2e/test_import_workflow.py
from typer.testing import CliRunner
from finlite.interfaces.cli.app import app

def test_full_import_workflow(tmp_path):
    runner = CliRunner()
    
    # 1. Init DB
    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0
    
    # 2. Import Nubank
    csv_file = tmp_path / "extrato.csv"
    csv_file.write_text("data,descricao,valor\n2025-01-10,Mercado,-50.00")
    
    result = runner.invoke(app, ["import", "nubank", str(csv_file)])
    assert result.exit_code == 0
    assert "Import completed" in result.stdout
    
    # 3. Apply rules
    result = runner.invoke(app, ["rules", "apply", "--auto"])
    assert result.exit_code == 0
    
    # 4. Post pending
    result = runner.invoke(app, ["post", "pending", "--auto"])
    assert result.exit_code == 0
    
    # 5. Generate report
    result = runner.invoke(app, ["report", "cashflow", "--month", "2025-01"])
    assert result.exit_code == 0
    assert "Mercado" in result.stdout or "Groceries" in result.stdout
```

## Regras

1. **CLI não conhece domain entities** - apenas DTOs (Commands/Results)
2. **Sem SQL/ORM aqui** - delega 100% para application layer
3. **Presenters separados** - facilita trocar Rich → JSON → HTML
4. **DI resolve dependências** - CLI não instancia repositories

---

**Ver também**: `application/` (use cases), `shared/di.py` (container)
