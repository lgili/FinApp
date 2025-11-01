"""Seed multi-month demo data for the Finlite ledger.

This script bootstraps a realistic dataset (accounts, ledger transactions,
statement inbox entries) so the Textual TUI can demonstrate dashboards and
workflows without requiring users to manually import data first.

Usage (from repo root):

    poetry run python backend/scripts/seed_demo_data.py --database-url sqlite:///var/demo.db

By default the script targets the configured Finlite settings database.
The seed is idempotent – running it multiple times will not duplicate data.
"""

from __future__ import annotations

import calendar
import hashlib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import typer

from finlite.application.dtos import (
    AccountDTO,
    CreateAccountDTO,
    CreatePostingDTO,
    CreateTransactionDTO,
)
from finlite.application.use_cases import (
    CreateAccountUseCase,
    ListAccountsUseCase,
    ListTransactionsUseCase,
    RecordTransactionUseCase,
)
from finlite.domain.entities.import_batch import ImportBatch, ImportSource, ImportStatus
from finlite.domain.entities.statement_entry import StatementEntry
from finlite.domain.exceptions import AccountAlreadyExistsError
from finlite.domain.value_objects.account_type import AccountType
from finlite.shared.di import Container, create_container, init_database
from finlite.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyImportBatchRepository,
    SqlAlchemyStatementEntryRepository,
)

app = typer.Typer(help="Seed the Finlite database with demo data for the TUI.")


# ---------------------------------------------------------------------------
# Data model declarations
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedAccount:
    code: str
    name: str
    type: AccountType
    currency: str = "BRL"
    card_issuer: str | None = None
    card_closing_day: int | None = None
    card_due_day: int | None = None


@dataclass(frozen=True)
class SeedPosting:
    account_code: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class SeedTransaction:
    key: str
    date: date
    description: str
    postings: tuple[SeedPosting, ...]
    note: str | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class SeedStatementEntry:
    key: str
    external_id: str
    occurred_at: datetime
    memo: str
    amount: Decimal
    currency: str
    payee: str | None = None
    suggested_account_code: str | None = None


@dataclass(frozen=True)
class SeedStatementBatch:
    key: str
    filename: str
    entries: tuple[SeedStatementEntry, ...]
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def file_sha256(self) -> str:
        return hashlib.sha256(self.key.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SeedDataset:
    accounts: tuple[SeedAccount, ...]
    transactions: tuple[SeedTransaction, ...]
    statement_batches: tuple[SeedStatementBatch, ...]


# ---------------------------------------------------------------------------
# Helpers for calendar math
# ---------------------------------------------------------------------------


def first_day_of_month(value: date) -> date:
    return date(value.year, value.month, 1)


def add_months(value: date, offset: int) -> date:
    month_index = value.month - 1 + offset
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def month_label(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


# ---------------------------------------------------------------------------
# Dataset builder
# ---------------------------------------------------------------------------


class DemoDatasetBuilder:
    """Generate a deterministic multi-month dataset."""

    def __init__(self, start_month: date, months: int, currency: str) -> None:
        if months < 2:
            raise ValueError("At least two months are required (one for history, one for inbox data).")
        self.start_month = first_day_of_month(start_month)
        self.months = months
        self.currency = currency.upper()

    def build(self) -> SeedDataset:
        accounts = self._build_accounts()
        transactions = self._build_transactions()
        statement_batches = self._build_statement_batches()
        return SeedDataset(accounts=accounts, transactions=transactions, statement_batches=statement_batches)

    def _build_accounts(self) -> tuple[SeedAccount, ...]:
        currency = self.currency
        return (
            SeedAccount(code="Assets:Checking", name="Main Checking", type=AccountType.ASSET, currency=currency),
            SeedAccount(code="Assets:Savings", name="Emergency Fund", type=AccountType.ASSET, currency=currency),
            SeedAccount(code="Assets:Investments", name="Brokerage Account", type=AccountType.ASSET, currency=currency),
            SeedAccount(
                code="Liabilities:CreditCard:Visa",
                name="Visa Credit Card",
                type=AccountType.LIABILITY,
                currency=currency,
                card_issuer="Finlite Bank",
                card_closing_day=25,
                card_due_day=5,
            ),
            SeedAccount(code="Income:Salary", name="Salary", type=AccountType.INCOME, currency=currency),
            SeedAccount(code="Income:Investments:Dividends", name="Investment Dividends", type=AccountType.INCOME, currency=currency),
            SeedAccount(code="Expenses:Housing:Rent", name="Rent", type=AccountType.EXPENSE, currency=currency),
            SeedAccount(code="Expenses:Groceries", name="Groceries", type=AccountType.EXPENSE, currency=currency),
            SeedAccount(code="Expenses:Utilities:Electric", name="Electric Utility", type=AccountType.EXPENSE, currency=currency),
            SeedAccount(code="Expenses:Dining", name="Dining Out", type=AccountType.EXPENSE, currency=currency),
            SeedAccount(code="Expenses:Transportation:RideShare", name="Ride Share", type=AccountType.EXPENSE, currency=currency),
            SeedAccount(code="Expenses:Entertainment:Streaming", name="Streaming Services", type=AccountType.EXPENSE, currency=currency),
        )

    def _build_transactions(self) -> tuple[SeedTransaction, ...]:
        history_months = [add_months(self.start_month, offset) for offset in range(self.months - 1)]
        transactions: list[SeedTransaction] = []
        for index, month_start in enumerate(history_months):
            label = month_label(month_start)
            transactions.extend(self._transactions_for_month(index, month_start, label))
        return tuple(transactions)

    def _transactions_for_month(self, index: int, month_start: date, label: str) -> list[SeedTransaction]:
        currency = self.currency
        tags = ("seed", f"period:{label}")

        salary_amount = Decimal("6500.00") + Decimal(index) * Decimal("45.00")
        rent_amount = Decimal("2300.00")
        groceries_amount = Decimal("520.00") + Decimal(index) * Decimal("12.50")
        utilities_amount = Decimal("210.00") + Decimal((index % 3) * 5)
        dining_amount = Decimal("140.00") + Decimal((index % 2) * 20)
        rideshare_amount = Decimal("80.00") + Decimal(5 * (index % 4))
        streaming_amount = Decimal("45.00")
        savings_transfer = Decimal("400.00") + Decimal(25 * (index % 3))
        credit_card_payment = Decimal("900.00") + Decimal(35 * (index % 4))

        month_transactions = [
            SeedTransaction(
                key=f"{label}-salary",
                date=month_start,
                description=f"Salary for {month_start:%B %Y}",
                postings=(
                    SeedPosting("Assets:Checking", salary_amount, currency),
                    SeedPosting("Income:Salary", -salary_amount, currency),
                ),
                tags=tags + ("category:income",),
            ),
            SeedTransaction(
                key=f"{label}-rent",
                date=month_start + timedelta(days=4),
                description="Monthly rent payment",
                postings=(
                    SeedPosting("Expenses:Housing:Rent", rent_amount, currency),
                    SeedPosting("Assets:Checking", -rent_amount, currency),
                ),
                tags=tags + ("category:rent",),
            ),
            SeedTransaction(
                key=f"{label}-groceries",
                date=month_start + timedelta(days=10),
                description="Groceries and household supplies",
                postings=(
                    SeedPosting("Expenses:Groceries", groceries_amount, currency),
                    SeedPosting("Assets:Checking", -groceries_amount, currency),
                ),
                tags=tags + ("category:groceries",),
            ),
            SeedTransaction(
                key=f"{label}-utilities",
                date=month_start + timedelta(days=16),
                description="Electric utility bill",
                postings=(
                    SeedPosting("Expenses:Utilities:Electric", utilities_amount, currency),
                    SeedPosting("Assets:Checking", -utilities_amount, currency),
                ),
                tags=tags + ("category:utilities",),
            ),
            SeedTransaction(
                key=f"{label}-dining",
                date=month_start + timedelta(days=18),
                description="Dining out",
                postings=(
                    SeedPosting("Expenses:Dining", dining_amount, currency),
                    SeedPosting("Assets:Checking", -dining_amount, currency),
                ),
                tags=tags + ("category:dining",),
            ),
            SeedTransaction(
                key=f"{label}-rideshare",
                date=month_start + timedelta(days=22),
                description="Ride share and transport",
                postings=(
                    SeedPosting("Expenses:Transportation:RideShare", rideshare_amount, currency),
                    SeedPosting("Assets:Checking", -rideshare_amount, currency),
                ),
                tags=tags + ("category:transport",),
            ),
            SeedTransaction(
                key=f"{label}-streaming",
                date=month_start + timedelta(days=24),
                description="Streaming subscriptions",
                postings=(
                    SeedPosting("Expenses:Entertainment:Streaming", streaming_amount, currency),
                    SeedPosting("Assets:Checking", -streaming_amount, currency),
                ),
                tags=tags + ("category:entertainment",),
            ),
            SeedTransaction(
                key=f"{label}-savings-transfer",
                date=month_start + timedelta(days=26),
                description="Transfer to savings",
                postings=(
                    SeedPosting("Assets:Savings", savings_transfer, currency),
                    SeedPosting("Assets:Checking", -savings_transfer, currency),
                ),
                tags=tags + ("category:transfer",),
            ),
            SeedTransaction(
                key=f"{label}-credit-card-payment",
                date=month_start + timedelta(days=27),
                description="Credit card payment",
                postings=(
                    SeedPosting("Liabilities:CreditCard:Visa", credit_card_payment, currency),
                    SeedPosting("Assets:Checking", -credit_card_payment, currency),
                ),
                tags=tags + ("category:credit-card",),
            ),
        ]

        if index % 2 == 0:
            dividend_amount = Decimal("180.00") + Decimal(index * 10)
            month_transactions.append(
                SeedTransaction(
                    key=f"{label}-dividends",
                    date=month_start + timedelta(days=12),
                    description="Quarterly dividend",
                    postings=(
                        SeedPosting("Assets:Investments", dividend_amount, currency),
                        SeedPosting("Income:Investments:Dividends", -dividend_amount, currency),
                    ),
                    tags=tags + ("category:investments",),
                )
            )

        return month_transactions

    def _build_statement_batches(self) -> tuple[SeedStatementBatch, ...]:
        statement_month = add_months(self.start_month, self.months - 1)
        label = month_label(statement_month)
        entries = [
            SeedStatementEntry(
                key=f"{label}-coffee",
                external_id=f"seed-{label}-coffee",
                occurred_at=datetime(statement_month.year, statement_month.month, 3, 14, 20, tzinfo=UTC),
                memo="Local cafe latte",
                amount=Decimal("-18.50"),
                currency=self.currency,
                payee="Roast Cafe",
                suggested_account_code="Expenses:Dining",
            ),
            SeedStatementEntry(
                key=f"{label}-grocery",
                external_id=f"seed-{label}-grocery",
                occurred_at=datetime(statement_month.year, statement_month.month, 5, 17, 45, tzinfo=UTC),
                memo="Neighborhood market",
                amount=Decimal("-92.35"),
                currency=self.currency,
                payee="Green Grocery",
                suggested_account_code="Expenses:Groceries",
            ),
            SeedStatementEntry(
                key=f"{label}-rideshare",
                external_id=f"seed-{label}-rideshare",
                occurred_at=datetime(statement_month.year, statement_month.month, 8, 7, 30, tzinfo=UTC),
                memo="Airport transfer",
                amount=Decimal("-48.00"),
                currency=self.currency,
                payee="MoveFast",
                suggested_account_code="Expenses:Transportation:RideShare",
            ),
            SeedStatementEntry(
                key=f"{label}-subscription",
                external_id=f"seed-{label}-subscription",
                occurred_at=datetime(statement_month.year, statement_month.month, 9, 12, 0, tzinfo=UTC),
                memo="Productivity suite subscription",
                amount=Decimal("-32.00"),
                currency=self.currency,
                payee="CloudApps",
                suggested_account_code="Expenses:Entertainment:Streaming",
            ),
            SeedStatementEntry(
                key=f"{label}-reimbursement",
                external_id=f"seed-{label}-reimbursement",
                occurred_at=datetime(statement_month.year, statement_month.month, 11, 15, 15, tzinfo=UTC),
                memo="Client expense reimbursement",
                amount=Decimal("120.00"),
                currency=self.currency,
                payee="ACME Consulting",
                suggested_account_code="Income:Salary",
            ),
        ]
        batch = SeedStatementBatch(
            key=f"seed-batch-{label}",
            filename=f"seed-demo-{label}.csv",
            entries=tuple(entries),
            metadata={"period": label, "seed": "demo"},
        )
        return (batch,)


# ---------------------------------------------------------------------------
# Seeding service
# ---------------------------------------------------------------------------


class DemoDataSeeder:
    """Apply the seed dataset using application use cases and repositories."""

    def __init__(self, container: Container, dataset: SeedDataset) -> None:
        self.container = container
        self.dataset = dataset

    def run(self) -> None:
        accounts_map = self._ensure_accounts()
        self._ensure_transactions()
        self._ensure_statement_entries(accounts_map)

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    def _ensure_accounts(self) -> dict[str, AccountDTO]:
        list_accounts_uc: ListAccountsUseCase = self.container.list_accounts_use_case()
        existing = {account.code: account for account in list_accounts_uc.execute()}

        create_uc: CreateAccountUseCase = self.container.create_account_use_case()
        created = False
        for account in self.dataset.accounts:
            if account.code in existing:
                continue
            dto = CreateAccountDTO(
                code=account.code,
                name=account.name,
                type=account.type.value,
                currency=account.currency,
                card_issuer=account.card_issuer,
                card_closing_day=account.card_closing_day,
                card_due_day=account.card_due_day,
            )
            try:
                create_uc.execute(dto)
                created = True
                typer.echo(f"Created account {account.code}")
            except AccountAlreadyExistsError:
                continue

        if created:
            existing = {account.code: account for account in list_accounts_uc.execute()}
        return existing

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    def _ensure_transactions(self) -> None:
        list_transactions_uc: ListTransactionsUseCase = self.container.list_transactions_use_case()
        existing_transactions = list_transactions_uc.execute()
        existing_keys = {
            tag.split(":", 1)[1]
            for txn in existing_transactions
            for tag in txn.tags
            if tag.startswith("seed:")
        }

        record_uc: RecordTransactionUseCase = self.container.record_transaction_use_case()
        for transaction in self.dataset.transactions:
            if transaction.key in existing_keys:
                continue

            dto = CreateTransactionDTO(
                date=transaction.date,
                description=transaction.description,
                postings=tuple(
                    CreatePostingDTO(
                        account_code=posting.account_code,
                        amount=posting.amount,
                        currency=posting.currency,
                    )
                    for posting in transaction.postings
                ),
                tags=("seed", f"seed:{transaction.key}") + transaction.tags,
                note=transaction.note,
            )
            record_uc.execute(dto)
            existing_keys.add(transaction.key)
            typer.echo(f"Recorded transaction {transaction.description} ({transaction.key})")

    # ------------------------------------------------------------------
    # Statement entries
    # ------------------------------------------------------------------

    def _ensure_statement_entries(self, accounts_map: dict[str, AccountDTO]) -> None:
        if not self.dataset.statement_batches:
            return

        scoped_session = self.container.session_factory()
        session = scoped_session()
        try:
            batch_repo = SqlAlchemyImportBatchRepository(session)
            entry_repo = SqlAlchemyStatementEntryRepository(session)

            for batch in self.dataset.statement_batches:
                existing_batch = batch_repo.find_by_filename(batch.filename)
                if existing_batch:
                    batch_id = existing_batch.id
                    current_entries = {
                        entry.external_id: entry for entry in entry_repo.find_by_batch(batch_id)
                    }
                else:
                    import_batch = ImportBatch.create(
                        source=ImportSource.MANUAL,
                        filename=batch.filename,
                        file_sha256=batch.file_sha256,
                        metadata=batch.metadata | {"seed": batch.key},
                    )
                    batch_repo.add(import_batch)
                    batch_id = import_batch.id
                    current_entries = {}

                added = 0
                for entry in batch.entries:
                    if entry.external_id in current_entries:
                        continue

                    statement_entry = StatementEntry.create(
                        batch_id=batch_id,
                        external_id=entry.external_id,
                        memo=entry.memo,
                        amount=entry.amount,
                        currency=entry.currency,
                        occurred_at=entry.occurred_at,
                        payee=entry.payee,
                        metadata={"seed": entry.key},
                    )
                    if entry.suggested_account_code:
                        account = accounts_map.get(entry.suggested_account_code)
                        if account:
                            statement_entry.suggest_account(account.id)
                    entry_repo.add(statement_entry)
                    added += 1

                if added:
                    persisted_batch = batch_repo.get(batch_id)
                    total_entries = len(entry_repo.find_by_batch(batch_id))
                    if persisted_batch.status == ImportStatus.PENDING:
                        persisted_batch.mark_completed(transaction_count=total_entries)
                    else:
                        persisted_batch.transaction_count = total_entries
                        persisted_batch.updated_at = datetime.now(tz=UTC)
                    batch_repo.update(persisted_batch)
                    typer.echo(f"Added {added} inbox entries to batch {batch.filename}")

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            scoped_session.remove()


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def resolve_start_month(months: int, explicit: str | None) -> date:
    if explicit:
        try:
            year, month = explicit.split("-", 1)
            return date(int(year), int(month), 1)
        except Exception as exc:  # noqa: BLE001
            raise typer.BadParameter("start-month must be in YYYY-MM format") from exc

    today = date.today()
    end_month = first_day_of_month(today)
    return add_months(end_month, -(months - 1))


@app.command()
def seed(
    months: int = typer.Option(6, min=2, help="Total months of data to synthesize (last month is kept as pending statements)."),
    start_month: str | None = typer.Option(None, help="Optional start month in YYYY-MM format."),
    currency: str = typer.Option("BRL", help="Three-letter currency code."),
    database_url: str | None = typer.Option(None, help="SQLAlchemy database URL to seed."),
    echo_sql: bool = typer.Option(False, "--echo-sql", help="Enable SQLAlchemy SQL echo for troubleshooting."),
) -> None:
    """Seed the Finlite database with deterministic demo data."""

    resolved_start = resolve_start_month(months, start_month)
    dataset = DemoDatasetBuilder(resolved_start, months, currency).build()

    if database_url is None:
        from finlite.config import get_settings

        settings = get_settings()
        database_url = settings.database_url
        typer.echo(f"Using default database at {database_url}")
    else:
        typer.echo(f"Using database URL {database_url}")

    container = create_container(database_url=database_url, echo=echo_sql)
    init_database(container)

    seeder = DemoDataSeeder(container, dataset)
    seeder.run()
    typer.echo("Seeding completed.")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    app()
