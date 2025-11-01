from __future__ import annotations

from datetime import date

from finlite.shared.di import create_container, init_database
from finlite.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyStatementEntryRepository,
)

from backend.scripts.seed_demo_data import DemoDataSeeder, DemoDatasetBuilder


def _collect_seed_tags(transactions) -> set[str]:
    tags: set[str] = set()
    for txn in transactions:
        tags.update(tag for tag in txn.tags if tag.startswith("seed:"))
    return tags


def test_seed_demo_data_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "demo.db"
    database_url = f"sqlite:///{db_path}"

    container = create_container(database_url)
    init_database(container)

    dataset = DemoDatasetBuilder(start_month=date(2024, 1, 1), months=6, currency="BRL").build()
    seeder = DemoDataSeeder(container, dataset)

    seeder.run()

    accounts = container.list_accounts_use_case().execute()
    account_codes = {account.code for account in accounts}
    assert "Assets:Checking" in account_codes
    assert "Expenses:Groceries" in account_codes

    transactions = container.list_transactions_use_case().execute()
    seed_tags_first = _collect_seed_tags(transactions)
    expected_tags = {f"seed:{txn.key}" for txn in dataset.transactions}
    assert seed_tags_first == expected_tags

    seeder.run()
    rerun_transactions = container.list_transactions_use_case().execute()
    seed_tags_second = _collect_seed_tags(rerun_transactions)
    assert seed_tags_second == seed_tags_first

    session_factory = container.session_factory()
    session = session_factory()
    try:
        entry_repo = SqlAlchemyStatementEntryRepository(session)
        pending = entry_repo.find_pending()
        expected_entries = sum(len(batch.entries) for batch in dataset.statement_batches)
        assert len(pending) == expected_entries
    finally:
        session.close()
        session_factory.remove()
