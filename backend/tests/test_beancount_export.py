from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.core.accounts import AccountType
from finlite.core.transactions import PostingCreate, TransactionCreate, create_transaction
from finlite.db.models import Account
from finlite.export.beancount import export_beancount


def _get_account(session: Session, account_type: AccountType) -> Account:
    stmt = select(Account).where(Account.type == account_type).limit(1)
    return session.scalars(stmt).one()


def test_beancount_export_single_transaction(seeded_session: Session) -> None:
    session = seeded_session
    asset = _get_account(session, AccountType.ASSET)
    income = _get_account(session, AccountType.INCOME)

    create_transaction(
        session,
        TransactionCreate(
            description="Salary",
            occurred_at=datetime(2025, 8, 15, tzinfo=UTC),
            reference="payroll-2025-08",
            postings=[
                PostingCreate(
                    account_id=asset.id,
                    amount=Decimal("1000"),
                    currency="BRL",
                ),
                PostingCreate(
                    account_id=income.id,
                    amount=Decimal("-1000"),
                    currency="BRL",
                    memo="Employer",
                ),
            ],
            extra={"note": "August salary"},
        ),
    )

    handle = StringIO()
    export_beancount(session, handle, "BRL")
    output = handle.getvalue().splitlines()

    assert output[0] == 'option "title" "Finlite Ledger"'
    assert output[1] == 'option "operating_currency" "BRL"'
    assert '2025-08-15 * "Salary" ; ref:payroll-2025-08' in output
    assert any(line.strip().startswith(asset.name) and "1000" in line for line in output)
    assert any("; Employer" in line for line in output)
    assert any(line.startswith("  ; note: August salary") for line in output)
