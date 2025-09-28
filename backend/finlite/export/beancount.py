"""Beancount export helpers."""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TextIO

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from finlite.db.models import Posting, Transaction

_DECIMAL_QUANT = Decimal("0.0001")


def _format_decimal(amount: Decimal) -> str:
    normalized = amount.quantize(_DECIMAL_QUANT, rounding=ROUND_HALF_UP)
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def export_beancount(session: Session, handle: TextIO, operating_currency: str) -> None:
    """Write all transactions in Beancount journal format."""
    handle.write('option "title" "Finlite Ledger"\n')
    handle.write(f'option "operating_currency" "{operating_currency}"\n\n')

    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.postings).joinedload(Posting.account))
        .order_by(Transaction.occurred_at, Transaction.id)
    )
    result = session.execute(stmt)
    transactions = result.scalars().unique().all()

    for txn in transactions:
        occurred = txn.occurred_at
        date_str = occurred.date().isoformat() if isinstance(occurred, datetime) else str(occurred)
        header = f'{date_str} * "{txn.description}"'
        if txn.reference:
            header += f" ; ref:{txn.reference}"
        handle.write(header + "\n")

        for posting in sorted(txn.postings, key=lambda item: item.id or 0):
            amount_text = _format_decimal(posting.amount)
            line = f"  {posting.account.name:<40} {amount_text} {posting.currency}"
            if posting.memo:
                line += f" ; {posting.memo}"
            handle.write(line + "\n")

        if txn.extra:
            for key, value in sorted(txn.extra.items()):
                handle.write(f"  ; {key}: {value}\n")

        handle.write("\n")
