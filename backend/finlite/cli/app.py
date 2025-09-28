"""Typer CLI entrypoint for finlite."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finlite.config import Settings, get_settings
from finlite.core.accounts import (
    AccountCreate,
    AccountType,
    create_account,
    list_accounts,
    seed_default_chart,
)
from finlite.core.transactions import PostingCreate, TransactionCreate, create_transaction
from finlite.db.migrator import upgrade_head
from finlite.db.models import Account, StatementEntry, StatementStatus
from finlite.db.session import session_scope
from finlite.export.beancount import export_beancount
from finlite.ingest.nubank_csv import import_nubank_csv
from finlite.logging import get_logger
from finlite.reports import generate_cashflow
from finlite.rules.mapping import MapRule, add_rule, load_rules, match_account

console = Console()
get_logger(__name__)

app = typer.Typer(help="Finlite CLI — local-first double-entry accounting")
accounts_app = typer.Typer(help="Account management commands")
transactions_app = typer.Typer(help="Transaction commands")
report_app = typer.Typer(help="Reporting commands")
export_app = typer.Typer(help="Export commands")
import_app = typer.Typer(help="Import commands")
post_app = typer.Typer(help="Posting commands")
rules_app = typer.Typer(help="Rules commands (category mapping)")

app.add_typer(accounts_app, name="accounts")
app.add_typer(transactions_app, name="txn")
app.add_typer(report_app, name="report")
app.add_typer(export_app, name="export")
app.add_typer(import_app, name="import")
app.add_typer(post_app, name="post")
app.add_typer(rules_app, name="rules")


@dataclass(slots=True)
class _PostingInput:
    account_identifier: str
    amount: Decimal
    currency: str | None
    memo: str | None


CURRENCY_CODE_LEN = 3
MONTHS_PER_YEAR = 12


def _resolve_settings() -> Settings:
    return get_settings()


def _ensure_timezone(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_posting(raw: str) -> _PostingInput:
    if "=" not in raw:
        raise typer.BadParameter("Posting must follow ACCOUNT=AMOUNT [CURRENCY] [memo...]")
    account_part, remainder = raw.split("=", 1)
    account_identifier = account_part.strip()
    if not account_identifier:
        raise typer.BadParameter("Account identifier cannot be empty")

    tokens = remainder.strip().split()
    if not tokens:
        raise typer.BadParameter("Amount is required in posting definition")

    try:
        amount = Decimal(tokens[0])
    except InvalidOperation as exc:  # pragma: no cover - defensive
        raise typer.BadParameter(f"Invalid amount '{tokens[0]}'") from exc

    currency: str | None = None
    memo_tokens: list[str] = []
    if len(tokens) > 1:
        potential_currency = tokens[1].upper()
        if len(potential_currency) == CURRENCY_CODE_LEN and potential_currency.isalpha():
            currency = potential_currency
            memo_tokens = tokens[2:]
        else:
            memo_tokens = tokens[1:]
    memo = " ".join(memo_tokens) if memo_tokens else None
    return _PostingInput(
        account_identifier=account_identifier,
        amount=amount,
        currency=currency,
        memo=memo,
    )


def _get_account(session: Session, identifier: str) -> Account:
    account: Account | None = None
    if identifier.isdigit():
        account = session.get(Account, int(identifier))
    if account is None:
        stmt = select(Account).where(Account.name == identifier).limit(1)
        account = session.scalar(stmt)
    if account is None:
        raise typer.BadParameter(f"Unknown account '{identifier}'")
    return account


def _format_money(amount: Decimal, currency: str) -> str:
    quantized = amount.quantize(Decimal("0.01"))
    return f"{quantized:,.2f} {currency}"


def _month_bounds(month: str) -> tuple[datetime, datetime]:
    try:
        year_str, month_str = month.split("-", 1)
        year = int(year_str)
        month_num = int(month_str)
    except ValueError as exc:
        raise typer.BadParameter("Month must be in YYYY-MM format") from exc
    if not 1 <= month_num <= MONTHS_PER_YEAR:
        raise typer.BadParameter("Month number must be between 01 and 12")
    start = datetime(year, month_num, 1, tzinfo=UTC)
    if month_num == MONTHS_PER_YEAR:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, month_num + 1, 1, tzinfo=UTC)
    return start, end


def _resolve_period(
    month: str | None, start: datetime | None, end: datetime | None
) -> tuple[datetime, datetime]:
    if month:
        resolved_start, resolved_end = _month_bounds(month)
    else:
        if start is None:
            today = datetime.now(UTC)
            resolved_start = datetime(today.year, today.month, 1, tzinfo=UTC)
        else:
            resolved_start = _ensure_timezone(start)

        if end is None:
            month_num = resolved_start.month
            year = resolved_start.year
            if month_num == MONTHS_PER_YEAR:
                resolved_end = datetime(year + 1, 1, 1, tzinfo=UTC)
            else:
                resolved_end = datetime(year, month_num + 1, 1, tzinfo=UTC)
        else:
            resolved_end = _ensure_timezone(end)
    if resolved_end <= resolved_start:
        raise typer.BadParameter("--to must be after --from")
    return resolved_start, resolved_end


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
    currency: str = typer.Option("BRL", "--currency", help="Account currency"),
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


@transactions_app.command("add")
def add_transaction(
    description: Annotated[str, typer.Argument(help="Transaction description")],
    postings: Annotated[
        list[str],
        typer.Option(
            "--posting",
            "-p",
            help="Posting in the form ACCOUNT=AMOUNT [CURRENCY] [memo...]",
        ),
    ],
    occurred_at: Annotated[
        str | None, typer.Option("--occurred-at", help="When the transaction occurred (ISO 8601)")
    ] = None,
    reference: Annotated[str | None, typer.Option(help="Optional reference")] = None,
) -> None:
    """Create a transaction with explicit postings."""
    MIN_POSTINGS = 2
    if len(postings) < MIN_POSTINGS:
        raise typer.BadParameter("At least two postings are required", param_hint="--posting")

    parsed_postings = [_parse_posting(item) for item in postings]
    settings = _resolve_settings()
    # Parse occurred_at if provided as ISO string (supports timezone offsets)
    occurred_dt: datetime | None
    if occurred_at is None:
        occurred_dt = None
    else:
        try:
            occurred_dt = datetime.fromisoformat(occurred_at)
        except Exception as exc:
            raise typer.BadParameter(
                "--occurred-at must be an ISO 8601 datetime, e.g., 2025-08-01T08:00:00+00:00"
            ) from exc
    occurred = _ensure_timezone(occurred_dt)

    with session_scope(settings) as session:
        posting_payloads: list[PostingCreate] = []
        for posting in parsed_postings:
            account = _get_account(session, posting.account_identifier)
            currency = (posting.currency or account.currency).upper()
            if currency != account.currency.upper():
                msg = (
                    f"Currency '{currency}' does not match account "
                    f"'{account.name}' currency '{account.currency}'"
                )
                raise typer.BadParameter(msg)
            posting_payloads.append(
                PostingCreate(
                    account_id=account.id,
                    amount=posting.amount,
                    currency=currency,
                    memo=posting.memo,
                )
            )

        transaction = create_transaction(
            session,
            TransactionCreate(
                description=description,
                occurred_at=occurred,
                postings=posting_payloads,
                reference=reference,
            ),
        )
        console.print(
            f"Created transaction [bold]{transaction.description}[/bold] (id={transaction.id}) "
            f"with {len(transaction.postings)} postings."
        )


@report_app.command("cashflow")
def cashflow_report(
    month: Annotated[str | None, typer.Option("--month", help="Month in YYYY-MM format")] = None,
    start: Annotated[
        datetime | None, typer.Option("--from", help="Start datetime inclusive (ISO format)")
    ] = None,
    end: Annotated[
        datetime | None, typer.Option("--to", help="End datetime exclusive (ISO format)")
    ] = None,
    currency: Annotated[str | None, typer.Option("--currency", help="Currency code")] = None,
) -> None:
    """Display cashflow totals for a period."""
    settings = _resolve_settings()
    currency_code = (currency or settings.default_currency).upper()
    period_start, period_end = _resolve_period(month, start, end)

    with session_scope(settings) as session:
        report = generate_cashflow(session, period_start, period_end, currency_code)

    console.print(
        f"[bold]Cashflow[/bold] {report.start.date()} → {report.end.date()} ({report.currency})"
    )
    totals = Table(show_header=False)
    totals.add_column("Metric")
    totals.add_column("Amount", justify="right")
    totals.add_row("Income", _format_money(report.income.total, report.currency))
    totals.add_row("Expenses", _format_money(report.expenses.total, report.currency))
    totals.add_row("Net", _format_money(report.net, report.currency))
    console.print(totals)

    if report.income.rows:
        income_table = Table(title="Income", show_header=True)
        income_table.add_column("Account")
        income_table.add_column("Amount", justify="right")
        for row in report.income.rows:
            income_table.add_row(row.account_name, _format_money(row.amount, report.currency))
        console.print(income_table)

    if report.expenses.rows:
        expense_table = Table(title="Expenses", show_header=True)
        expense_table.add_column("Account")
        expense_table.add_column("Amount", justify="right")
        for row in report.expenses.rows:
            expense_table.add_row(row.account_name, _format_money(row.amount, report.currency))
        console.print(expense_table)


@export_app.command("beancount")
def export_beancount_cmd(
    output: Annotated[Path, typer.Argument(help="Destination .beancount file")],
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help="Overwrite existing file", is_flag=True),
    ] = False,
) -> None:
    """Export all transactions to a Beancount journal."""
    output_path = output if output.is_absolute() else Path.cwd() / output
    if output_path.exists() and not overwrite:
        raise typer.BadParameter(
            f"File {output_path} already exists. Use --overwrite to replace it."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    settings = _resolve_settings()
    with session_scope(settings) as session, output_path.open("w", encoding="utf-8") as handle:
        export_beancount(session, handle, settings.default_currency)

    console.print(f"Exported ledger to [bold]{output_path}[/bold].")


@import_app.command("nubank")
def import_nubank(
    csv_path: Annotated[Path, typer.Argument(help="Path to Nubank CSV file")],
    account: Annotated[
        str | None,
        typer.Option("--account", help="Account hint for entries"),
    ] = None,
) -> None:
    """Import a Nubank CSV into statement entries (Phase 2 primer)."""
    csv_path = csv_path if csv_path.is_absolute() else Path.cwd() / csv_path
    if not csv_path.exists():
        raise typer.BadParameter(f"File not found: {csv_path}")

    settings = _resolve_settings()
    with session_scope(settings) as session:
        batch = import_nubank_csv(
            session, csv_path, settings.default_currency, account_hint=account
        )
        # Compute count explicitly via COUNT to satisfy type-checker and avoid loading rows
        count = (
            session.scalar(
                select(func.count())
                .select_from(StatementEntry)
                .where(StatementEntry.batch_id == batch.id)
            )
            or 0
        )
        console.print(
            f"Imported [bold]{csv_path.name}[/bold] as batch id={batch.id} with {count} entries."
        )


def _find_account_by_name(session: Session, name: str) -> Account | None:
    stmt = select(Account).where(Account.name == name).limit(1)
    return session.scalar(stmt)


def _get_or_create_account(
    session: Session, name: str, type_: AccountType, currency: str
) -> Account:
    existing = _find_account_by_name(session, name)
    if existing is not None:
        return existing
    return create_account(session, AccountCreate(name=name, type=type_, currency=currency))


def _ensure_asset_account(session: Session, full_name: str, currency: str) -> Account:
    """Ensure an asset account exists for the given hierarchical name.

    - Accepts names like "Assets:Bank:Nubank" and creates intermediate nodes if missing.
    - Verifies currency matches when accounts already exist.
    """
    # If exact match exists, validate currency and return
    existing = _find_account_by_name(session, full_name)
    if existing is not None:
        if existing.currency.upper() != currency.upper():
            raise typer.BadParameter(
                f"Currency mismatch for asset '{existing.name}': {existing.currency} != {currency}"
            )
        return existing

    parts = full_name.split(":")
    built_name = []
    parent_id: int | None = None
    for _idx, part in enumerate(parts):
        built_name.append(part)
        current_name = ":".join(built_name)
        found = _find_account_by_name(session, current_name)
        if found is None:
            # Create this node
            created = create_account(
                session,
                AccountCreate(
                    name=current_name,
                    type=AccountType.ASSET,
                    currency=currency,
                    parent_id=parent_id,
                ),
            )
            parent_id = created.id
            found = created
        else:
            # Validate currency consistency
            if found.currency.upper() != currency.upper():
                raise typer.BadParameter(
                    f"Currency mismatch for asset '{found.name}': {found.currency} != {currency}"
                )
            parent_id = found.id
    # The last found/created is the leaf
    leaf = _find_account_by_name(session, full_name)
    assert leaf is not None
    return leaf


@post_app.command("pending")
def post_pending(
    asset: Annotated[
        str | None,
        typer.Option("--asset", help="Asset account to use for postings"),
    ] = None,
    batch_id: Annotated[
        int | None,
        typer.Option("--batch-id", help="Limit to a specific import batch"),
    ] = None,
) -> None:
    """Convert imported statement entries into balanced transactions."""
    settings = _resolve_settings()
    with session_scope(settings) as session:
        # Collect entries
        stmt = select(StatementEntry).where(StatementEntry.status == StatementStatus.IMPORTED)
        if batch_id is not None:
            stmt = stmt.where(StatementEntry.batch_id == batch_id)
        entries = session.scalars(stmt).all()
        if not entries:
            console.print("No pending entries to post.")
            return

        posted = 0
        for entry in entries:
            # Resolve asset account: CLI arg takes priority, then entry.extra hint
            asset_name = asset
            if asset_name is None and isinstance(entry.extra, dict):
                asset_name = entry.extra.get("account_hint")
            if not asset_name:
                raise typer.BadParameter(
                    "Asset account not specified. Provide --asset or import with --account hint."
                )
            asset_account = _ensure_asset_account(session, asset_name, entry.currency)

            # Determine category account and posting signs
            amount = entry.amount
            currency = entry.currency
            if amount < 0:
                # Expense: asset negative, expense positive
                mapped = match_account(settings, (entry.memo or entry.payee or ""), is_expense=True)
                category_name = mapped or "Expenses:Uncategorized"
                category = _get_or_create_account(
                    session, category_name, AccountType.EXPENSE, currency
                )
                postings = [
                    PostingCreate(account_id=asset_account.id, amount=amount, currency=currency),
                    PostingCreate(account_id=category.id, amount=-amount, currency=currency),
                ]
            else:
                # Income: asset positive, income negative
                mapped = match_account(
                    settings, (entry.memo or entry.payee or ""), is_expense=False
                )
                category_name = mapped or "Income:Uncategorized"
                category = _get_or_create_account(
                    session, category_name, AccountType.INCOME, currency
                )
                postings = [
                    PostingCreate(account_id=asset_account.id, amount=amount, currency=currency),
                    PostingCreate(account_id=category.id, amount=-amount, currency=currency),
                ]

            description = entry.memo or "Imported"
            reference = f"import:{entry.batch_id}:{entry.external_id}"
            create_transaction(
                session,
                TransactionCreate(
                    description=description,
                    occurred_at=entry.occurred_at,
                    postings=postings,
                    reference=reference,
                ),
            )
            entry.status = StatementStatus.POSTED
            posted += 1

        console.print(f"Posted {posted} entries into transactions.")


@rules_app.command("add")
def rules_add(
    pattern: Annotated[str, typer.Argument(help="Substring to match in description/memo")],
    account: Annotated[str, typer.Argument(help="Target account name (e.g., Expenses:Groceries)")],
    type_: Annotated[AccountType, typer.Option("--type", help="expense or income")],
) -> None:
    """Add a simple description→account mapping rule."""
    if type_ not in (AccountType.EXPENSE, AccountType.INCOME):
        raise typer.BadParameter("--type must be 'expense' or 'income'")
    settings = _resolve_settings()
    add_rule(
        settings,
        MapRule(
            pattern=pattern,
            account=account,
            type="expense" if type_ == AccountType.EXPENSE else "income",
        ),
    )
    kind = "expense" if type_ == AccountType.EXPENSE else "income"
    console.print(f"Added mapping: '{pattern}' → {account} ({kind})")


@rules_app.command("list")
def rules_list() -> None:
    """List all mapping rules."""
    settings = _resolve_settings()
    rules = load_rules(settings)
    if not rules:
        console.print(
            "No rules configured yet. Add one with: fin rules add --type expense 'uber'\n"
            "Expenses:Transport"
        )
        return

    table = Table(title="Category Mapping Rules")
    table.add_column("Type", style="cyan")
    table.add_column("Pattern", style="magenta")
    table.add_column("Account", style="green")
    for r in rules:
        table.add_row(r.type, r.pattern, r.account)
    console.print(table)


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
