"""Typer CLI entrypoint for finlite."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
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
from finlite.db.models import Account, StatementEntry, StatementStatus, Transaction
from finlite.db.session import session_scope
from finlite.export.beancount import export_beancount
from finlite.ingest.nubank_csv import import_nubank_csv
from finlite.ingest.ofx import import_ofx
from finlite.logging import get_logger
from finlite.nlp.ask_agent import parse_intent
from finlite.nlp.intents import (
    ImportFileIntent,
    Intent,
    ListTransactionsIntent,
    MakeRuleIntent,
    PostPendingIntent,
    ReportCashflowIntent,
    ReportCategoryIntent,
)
from finlite.reports import generate_cashflow
from finlite.rules.mapping import MapRule, add_rule, find_matching_rule, load_rules, match_account

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
ask_app = typer.Typer(help="Natural language to intent (preview first)")

app.add_typer(accounts_app, name="accounts")
app.add_typer(transactions_app, name="txn")
app.add_typer(report_app, name="report")
app.add_typer(export_app, name="export")
app.add_typer(import_app, name="import")
app.add_typer(post_app, name="post")
app.add_typer(rules_app, name="rules")
app.add_typer(ask_app, name="ask")


@dataclass(slots=True)
class _PostingInput:
    account_identifier: str
    amount: Decimal
    currency: str | None
    memo: str | None


CURRENCY_CODE_LEN = 3
MONTHS_PER_YEAR = 12
DEFAULT_TXN_LIST_LIMIT = 20


def _calculate_rule_coverage(
    entries: Sequence[StatementEntry],
    rules: Sequence[MapRule],
) -> tuple[list[tuple[int, MapRule, int]], int]:
    rule_match_counts = [0 for _ in rules]
    matched_entries = 0
    for entry in entries:
        text = entry.memo or entry.payee or ""
        match = find_matching_rule(
            rules,
            text,
            is_expense=entry.amount < 0,
            amount=entry.amount,
            occurred_at=entry.occurred_at,
        )
        if match is None:
            continue
        idx, _ = match
        rule_match_counts[idx] += 1
        matched_entries += 1

    coverage_rows = [
        (idx, rules[idx], count) for idx, count in enumerate(rule_match_counts) if count > 0
    ]
    return coverage_rows, matched_entries


def _print_rule_coverage_report(
    entries: Sequence[StatementEntry],
    coverage_rows: Sequence[tuple[int, MapRule, int]],
    matched_entries: int,
) -> None:
    total_entries = len(entries)
    if coverage_rows:
        coverage_table = Table(title="Rule Coverage")
        coverage_table.add_column("#", justify="right")
        coverage_table.add_column("Pattern")
        coverage_table.add_column("Account")
        coverage_table.add_column("Matches", justify="right")
        coverage_table.add_column("Share", justify="right")

        for idx, rule, count in coverage_rows:
            share = f"{(count / total_entries * 100):.1f}%" if total_entries else "0.0%"
            coverage_table.add_row(
                str(idx + 1),
                rule.pattern,
                rule.account,
                str(count),
                share,
            )
        console.print(coverage_table)
    else:
        console.print("No entries currently match any configured rule.")

    coverage_share = f"{(matched_entries / total_entries * 100):.1f}%" if total_entries else "0.0%"
    without_match = total_entries - matched_entries
    without_share = f"{(without_match / total_entries * 100):.1f}%" if total_entries else "0.0%"
    console.print(f"Entries covered by rules: {matched_entries} ({coverage_share})")
    console.print(f"Entries without rule match: {without_match} ({without_share})")


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


@transactions_app.command("list")
def list_transactions(  # noqa: PLR0913 - CLI filters are user-facing options
    limit: Annotated[
        int, typer.Option("--limit", min=1, max=100, help="Maximum rows to display")
    ] = DEFAULT_TXN_LIST_LIMIT,
    text: Annotated[
        str | None, typer.Option("--text", help="Filter by description substring")
    ] = None,
    account: Annotated[str | None, typer.Option("--account", help="Filter by account name")] = None,
    min_amount: Annotated[
        float | None,
        typer.Option("--min-amount", help="Minimum absolute amount to include"),
    ] = None,
    max_amount: Annotated[
        float | None,
        typer.Option("--max-amount", help="Maximum absolute amount to include"),
    ] = None,
    start: Annotated[
        datetime | None, typer.Option("--from", help="Start datetime inclusive (ISO format)")
    ] = None,
    end: Annotated[
        datetime | None, typer.Option("--to", help="End datetime inclusive (ISO format)")
    ] = None,
) -> None:
    """List recent transactions with optional filters."""
    settings = _resolve_settings()
    start_dt = _ensure_timezone(start) if start else None
    end_dt = _ensure_timezone(end) if end else None
    min_amount_dec = Decimal(str(min_amount)) if min_amount is not None else None
    max_amount_dec = Decimal(str(max_amount)) if max_amount is not None else None

    with session_scope(settings) as session:
        stmt = select(Transaction).order_by(Transaction.occurred_at.desc())
        if text:
            stmt = stmt.where(Transaction.description.ilike(f"%{text}%"))
        if start_dt is not None:
            stmt = stmt.where(Transaction.occurred_at >= start_dt)
        if end_dt is not None:
            stmt = stmt.where(Transaction.occurred_at <= end_dt)
        if account:
            stmt = stmt.join(Transaction.postings).join(Account).where(Account.name == account)
            stmt = stmt.distinct()
        stmt = stmt.limit(limit)
        transactions = session.scalars(stmt).all()

        if not transactions:
            console.print("No transactions found for the given filters.")
            return

        table = Table(title="Transactions")
        table.add_column("Date")
        table.add_column("Description")
        table.add_column("Accounts")
        table.add_column("Amounts", justify="right")

        for txn in transactions:
            accounts = ", ".join(sorted({posting.account.name for posting in txn.postings}))
            totals: dict[str, Decimal] = {}
            for posting in txn.postings:
                totals.setdefault(posting.currency, Decimal("0"))
                totals[posting.currency] += posting.amount
            if min_amount_dec is not None or max_amount_dec is not None:
                abs_total = max((abs(val) for val in totals.values()), default=Decimal("0"))
                if min_amount_dec is not None and abs_total < min_amount_dec:
                    continue
                if max_amount_dec is not None and abs_total > max_amount_dec:
                    continue
            amount_str = ", ".join(
                f"{value.quantize(Decimal('0.01')):+,.2f} {currency}"
                for currency, value in sorted(totals.items())
            )
            table.add_row(
                txn.occurred_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M"),
                txn.description,
                accounts or "-",
                amount_str or "-",
            )

    console.print(table)


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


@report_app.command("category")
def report_category(
    category: Annotated[str, typer.Argument(help="Account/category name to summarise")],
    month: Annotated[str | None, typer.Option("--month", help="Month in YYYY-MM format")] = None,
    start: Annotated[
        datetime | None, typer.Option("--from", help="Start datetime inclusive (ISO format)")
    ] = None,
    end: Annotated[
        datetime | None, typer.Option("--to", help="End datetime exclusive (ISO format)")
    ] = None,
    currency: Annotated[str | None, typer.Option("--currency", help="Currency code")] = None,
) -> None:
    """Display the cashflow total for a single category/account."""
    settings = _resolve_settings()
    currency_code = (currency or settings.default_currency).upper()
    period_start, period_end = _resolve_period(month, start, end)

    with session_scope(settings) as session:
        report = generate_cashflow(session, period_start, period_end, currency_code)

    target = None
    for section in (report.expenses.rows, report.income.rows):
        for row in section:
            if row.account_name.lower() == category.lower():
                target = row
                break
        if target:
            break

    if target is None:
        not_found_msg = (
            f"No totals found for [bold]{category}[/bold] between {period_start.date()} "
            f"and {period_end.date()}"
        )
        console.print(not_found_msg)
        return

    console.print(
        f"[bold]{target.account_name}[/bold] — {_format_money(target.amount, currency_code)}"
    )


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


@import_app.command("ofx")
def import_ofx_cmd(
    ofx_path: Annotated[Path, typer.Argument(help="Path to OFX file")],
    account: Annotated[
        str | None,
        typer.Option("--account", help="Account hint for entries"),
    ] = None,
) -> None:
    """Import an OFX file into statement entries."""
    ofx_path = ofx_path if ofx_path.is_absolute() else Path.cwd() / ofx_path
    if not ofx_path.exists():
        raise typer.BadParameter(f"File not found: {ofx_path}")

    settings = _resolve_settings()
    with session_scope(settings) as session:
        batch = import_ofx(session, ofx_path, settings.default_currency, account_hint=account)
        count = (
            session.scalar(
                select(func.count())
                .select_from(StatementEntry)
                .where(StatementEntry.batch_id == batch.id)
            )
            or 0
        )
        console.print(
            f"Imported [bold]{ofx_path.name}[/bold] as batch id={batch.id} with {count} entries."
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
            # Prefer suggested account if present and valid
            suggested: Account | None = None
            if entry.suggested_account_id is not None:
                suggested = session.get(Account, entry.suggested_account_id)

            if amount < 0:
                # Expense: asset negative, expense positive
                mapped = (
                    suggested.name
                    if suggested
                    else match_account(
                        settings,
                        (entry.memo or entry.payee or ""),
                        is_expense=True,
                        amount=entry.amount,
                        occurred_at=entry.occurred_at,
                    )
                )
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
                mapped = (
                    suggested.name
                    if suggested
                    else match_account(
                        settings,
                        (entry.memo or entry.payee or ""),
                        is_expense=False,
                        amount=entry.amount,
                        occurred_at=entry.occurred_at,
                    )
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
def rules_add(  # noqa: PLR0913 - CLI command with multiple options is acceptable
    pattern: Annotated[str, typer.Argument(help="Substring or regex to match")],
    account: Annotated[str, typer.Argument(help="Target account name (e.g., Expenses:Groceries)")],
    type_: Annotated[AccountType, typer.Option("--type", help="expense or income")],
    regex: Annotated[bool, typer.Option("--regex", help="Treat pattern as regex")] = False,
    min_amount: Annotated[
        float | None, typer.Option("--min-amount", help="Minimum absolute amount to match")
    ] = None,
    max_amount: Annotated[
        float | None, typer.Option("--max-amount", help="Maximum absolute amount to match")
    ] = None,
    hour_start: Annotated[
        int | None, typer.Option("--hour-start", help="Start hour (0-23) inclusive")
    ] = None,
    hour_end: Annotated[
        int | None, typer.Option("--hour-end", help="End hour (0-23) inclusive")
    ] = None,
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
            regex=regex,
            min_amount=min_amount,
            max_amount=max_amount,
            hour_start=hour_start,
            hour_end=hour_end,
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
    table.add_column("Flags")
    table.add_column("Amount Range", justify="right")
    table.add_column("Hours", justify="right")
    for r in rules:
        flags: list[str] = []
        if r.regex:
            flags.append("regex")
        flags_str = ", ".join(flags) if flags else "-"
        if r.min_amount is not None:
            flags_str = f"{flags_str}, min" if flags_str != "-" else "min"
        if r.max_amount is not None:
            flags_str = f"{flags_str}, max" if flags_str != "-" else "max"
        if r.hour_start is not None or r.hour_end is not None:
            flags_str = f"{flags_str}, hour" if flags_str != "-" else "hour"

        amount_range = "-"
        if r.min_amount is not None or r.max_amount is not None:
            lower = f">={r.min_amount:.2f}" if r.min_amount is not None else "-"
            upper = f"<={r.max_amount:.2f}" if r.max_amount is not None else "-"
            amount_range = f"{lower} / {upper}"

        hours = "-"
        if r.hour_start is not None or r.hour_end is not None:
            start = f"{r.hour_start:02d}" if r.hour_start is not None else "00"
            end = f"{r.hour_end:02d}" if r.hour_end is not None else "23"
            hours = f"{start}-{end}"

        table.add_row(r.type, r.pattern, r.account, flags_str, amount_range, hours)
    console.print(table)


@rules_app.command("apply")
def rules_apply(
    auto: Annotated[
        bool, typer.Option("--auto", help="Apply suggestions and mark as matched")
    ] = True,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Preview results without modifying entries")
    ] = False,
) -> None:
    """Apply simple mapping rules to imported entries (suggest categories)."""
    settings = _resolve_settings()
    with session_scope(settings) as session:
        stmt = select(StatementEntry).where(StatementEntry.status == StatementStatus.IMPORTED)
        entries = session.scalars(stmt).all()
        if not entries:
            console.print("No imported entries to apply rules.")
            return

        matched = 0
        preview_rows: list[tuple[int, str, str]] = []  # (entry_id, text, mapped_account)
        for entry in entries:
            text = entry.memo or entry.payee or ""
            is_expense = entry.amount < 0
            mapped = match_account(
                settings,
                text,
                is_expense=is_expense,
                amount=entry.amount,
                occurred_at=entry.occurred_at,
            )
            if not mapped:
                continue
            # Ensure account exists and set as suggested
            acc_type = AccountType.EXPENSE if is_expense else AccountType.INCOME
            account = _get_or_create_account(session, mapped, acc_type, entry.currency)
            if dry_run:
                preview_rows.append((entry.id, text, account.name))
            else:
                entry.suggested_account_id = account.id
                if auto:
                    entry.status = StatementStatus.MATCHED
            matched += 1
        if dry_run:
            table = Table(title="Rules Apply Preview")
            table.add_column("Entry ID", justify="right")
            table.add_column("Text")
            table.add_column("Suggested Account")
            for eid, text, acc in preview_rows[:50]:
                table.add_row(str(eid), text[:80], acc)
            console.print(table)
            more = len(preview_rows) - min(len(preview_rows), 50)
            if more > 0:
                console.print(f"... and {more} more rows")
            console.print(f"Would match {matched} entries (no changes made).")
        else:
            console.print(f"Applied rules to {matched} entries.")


@rules_app.command("stats")
def rules_stats(
    batch_id: Annotated[
        int | None, typer.Option("--batch-id", help="Filter by a specific import batch")
    ] = None,
) -> None:
    """Show coverage metrics for statement entries and suggestions."""
    settings = _resolve_settings()
    with session_scope(settings) as session:
        stmt = select(StatementEntry)
        if batch_id is not None:
            stmt = stmt.where(StatementEntry.batch_id == batch_id)
        entries = session.scalars(stmt).all()
        if not entries:
            console.print("No statement entries found for the given filters.")
            return

        total = len(entries)
        status_counter = Counter(entry.status for entry in entries)
        suggested = sum(1 for entry in entries if entry.suggested_account_id is not None)
        matched = status_counter.get(StatementStatus.MATCHED, 0)
        posted = status_counter.get(StatementStatus.POSTED, 0)
        imported = status_counter.get(StatementStatus.IMPORTED, 0)
        unmatched = total - suggested

        def _share(count: int) -> str:
            return f"{(count / total * 100):.1f}%" if total else "0.0%"

        table = Table(title="Statement Entries Overview")
        table.add_column("Metric")
        table.add_column("Count", justify="right")
        table.add_column("Share", justify="right")
        table.add_row("Total", str(total), "100.0%")
        table.add_row("Imported", str(imported), _share(imported))
        table.add_row("Matched", str(matched), _share(matched))
        table.add_row("Posted", str(posted), _share(posted))
        table.add_row("Suggested", str(suggested), _share(suggested))
        table.add_row("Unmatched", str(unmatched), _share(unmatched))
        console.print(table)

        rules = load_rules(settings)
        if not rules:
            console.print(
                "No mapping rules configured yet. Add rules with `fin rules add` to track coverage."
            )
            return

        coverage_rows, matched_entries = _calculate_rule_coverage(entries, rules)
        _print_rule_coverage_report(entries, coverage_rows, matched_entries)


@ask_app.command()
def ask(  # noqa: PLR0912, PLR0915 - CLI dispatcher with multiple branches
    q: Annotated[str, typer.Argument(help="Natural language request")],
    explain: Annotated[
        bool, typer.Option("--explain", "-x", help="Show how it was parsed")
    ] = False,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Confirm execution when applicable")
    ] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview only; do not execute")] = True,
) -> None:
    """Parse NL query into an intent and show the equivalent CLI commands.

    This is preview-first. For now, we only print the deterministic commands that would run.
    """
    try:
        result = parse_intent(q)
    except Exception as exc:
        raise typer.BadParameter(f"Could not parse query: {exc}") from exc

    intent = result.intent

    def _preview(i: Intent) -> list[str]:  # noqa: PLR0912, PLR0911 - branching per intent type
        if isinstance(i, ImportFileIntent):
            path = i.path if Path(i.path).is_absolute() else str(Path.cwd() / i.path)
            return [
                f'fin import {i.source} {path} --account "{i.account}"',
            ]
        if isinstance(i, ReportCashflowIntent):
            if i.month:
                return [f"fin report cashflow --month {i.month}"]
            parts: list[str] = ["fin report cashflow"]
            if i.from_:
                parts += ["--from", i.from_]
            if i.to:
                parts += ["--to", i.to]
            return [" ".join(parts)]
        if isinstance(i, PostPendingIntent):
            return ["fin post pending --asset 'Assets:Bank:Nubank'"]
        if isinstance(i, ReportCategoryIntent):
            parts = ["fin report category", f'"{i.category}"']
            if i.month:
                parts += ["--month", i.month]
            if i.from_:
                parts += ["--from", i.from_]
            if i.to:
                parts += ["--to", i.to]
            return [" ".join(parts)]
        if isinstance(i, ListTransactionsIntent):
            parts = ["fin txn list"]
            if i.text:
                parts += ["--text", f'"{i.text}"']
            if i.account:
                parts += ["--account", f'"{i.account}"']
            if i.limit != DEFAULT_TXN_LIST_LIMIT:
                parts += ["--limit", str(i.limit)]
            if i.min_amount is not None:
                parts += ["--min-amount", str(i.min_amount)]
            if i.max_amount is not None:
                parts += ["--max-amount", str(i.max_amount)]
            if i.from_:
                parts += ["--from", i.from_]
            if i.to:
                parts += ["--to", i.to]
            return [" ".join(parts)]
        if isinstance(i, MakeRuleIntent):
            parts = [
                "fin rules add",
                f'"{i.pattern}"',
                f'"{i.account}"',
                "--type",
                i.type,
            ]
            if i.regex:
                parts.append("--regex")
            if i.min_amount is not None:
                parts += ["--min-amount", str(i.min_amount)]
            if i.max_amount is not None:
                parts += ["--max-amount", str(i.max_amount)]
            if i.hour_start is not None:
                parts += ["--hour-start", str(i.hour_start)]
            if i.hour_end is not None:
                parts += ["--hour-end", str(i.hour_end)]
            return [" ".join(parts)]
        return ["# Unknown intent"]

    cmds = _preview(intent)
    console.print("[bold]Preview[/bold]:")
    for c in cmds:
        console.print(f"  $ {c}")
    if explain:
        console.print(f"Parsed by: {result.source}")
        console.print(f"Intent: {type(intent).__name__}")

    # Execution placeholder: keep safe by default
    if not dry_run and yes:
        # Execute mapped action safely by calling internal commands
        if isinstance(intent, ImportFileIntent):
            csv = Path(intent.path)
            import_nubank(csv, account=intent.account)
        elif isinstance(intent, ReportCashflowIntent):
            # Only month is handled for now; from/to can be wired later
            cashflow_report(month=intent.month)
        elif isinstance(intent, PostPendingIntent):
            # Use a sensible default asset if none is provided via import hint
            post_pending(asset="Assets:Bank:Nubank")
        elif isinstance(intent, ReportCategoryIntent):
            start_dt = None
            end_dt = None
            if intent.from_:
                try:
                    start_dt = datetime.fromisoformat(intent.from_)
                except ValueError:
                    start_dt = None
            if intent.to:
                try:
                    end_dt = datetime.fromisoformat(intent.to)
                except ValueError:
                    end_dt = None
            report_category(
                category=intent.category,
                month=intent.month,
                start=start_dt,
                end=end_dt,
            )
        elif isinstance(intent, ListTransactionsIntent):

            def _maybe_parse(value: str | None) -> datetime | None:
                if value is None:
                    return None
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    return None

            list_transactions(
                limit=intent.limit,
                text=intent.text,
                account=intent.account,
                min_amount=intent.min_amount,
                max_amount=intent.max_amount,
                start=_maybe_parse(intent.from_),
                end=_maybe_parse(intent.to),
            )
        elif isinstance(intent, MakeRuleIntent):
            rules_add(
                intent.pattern,
                intent.account,
                AccountType.EXPENSE if intent.type == "expense" else AccountType.INCOME,
                regex=intent.regex,
                min_amount=intent.min_amount,
                max_amount=intent.max_amount,
                hour_start=intent.hour_start,
                hour_end=intent.hour_end,
            )
        else:  # pragma: no cover - defensive
            console.print("Unknown intent type; nothing executed.")


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
