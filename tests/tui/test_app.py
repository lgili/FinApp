import asyncio
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from finlite.application.dtos import CreateAccountDTO
from finlite.application.use_cases import CreateAccountUseCase
from finlite.domain.entities.statement_entry import StatementEntry, StatementStatus
from finlite.interfaces.tui.app import FinliteTUI
from finlite.shared.di import create_container, init_database


@pytest.fixture
def container(tmp_path):
    db_url = f"sqlite:///{tmp_path/'tui.db'}"
    container = create_container(db_url, echo=False)
    init_database(container)
    return container


def _seed_accounts(container):
    use_case: CreateAccountUseCase = container.create_account_use_case()
    use_case.execute(
        CreateAccountDTO(
            code="Assets:Bank:Checking",
            name="Checking",
            type="ASSET",
            currency="BRL",
        )
    )
    expense = use_case.execute(
        CreateAccountDTO(
            code="Expenses:Groceries",
            name="Groceries",
            type="EXPENSE",
            currency="BRL",
        )
    ).account
    return expense


def _seed_pending_entry(container, expense_account):
    entry = StatementEntry.create(
        batch_id=uuid4(),
        external_id="INV-001",
        memo="Groceries",
        amount=Decimal("-42.00"),
        currency="BRL",
        occurred_at=datetime(2025, 10, 5),
    )
    entry.suggest_account(expense_account.id)

    repo = container.statement_entry_repository()
    repo.add(entry)
    repo._session.commit()  # type: ignore[attr-defined]
    stored = repo.find_pending()
    return stored[0]


def test_launch_and_switch_views(container):
    expense = _seed_accounts(container)
    _seed_pending_entry(container, expense)

    app = FinliteTUI(container)
    async def run_test():
        async with app.run_test() as pilot:  # type: ignore[arg-type]
            await pilot.pause()
            assert app._active_view == "dashboard"

            await pilot.press("2")  # switch to inbox
            await pilot.pause()
            assert app._active_view == "inbox"

            await pilot.press("ctrl+k")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert app._active_view == "inbox"

    asyncio.run(run_test())


def test_post_entry_from_inbox(container):
    expense = _seed_accounts(container)
    entry = _seed_pending_entry(container, expense)

    app = FinliteTUI(container)
    async def run_test():
        async with app.run_test() as pilot:  # type: ignore[arg-type]
            await pilot.pause()
            await pilot.press("2")
            await pilot.pause()
            await pilot.press("a")
            await pilot.pause()

    asyncio.run(run_test())

    repo = container.statement_entry_repository()
    posted = repo.find_by_status(StatementStatus.POSTED)
    posted_ids = {item.id for item in posted}
    assert entry.id in posted_ids
