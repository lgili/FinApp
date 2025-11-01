"""Ledger view for recent transactions."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from textual.widgets import DataTable

from finlite.application.dtos import TransactionDTO


class LedgerView(DataTable):
    """Table listing recent transactions."""

    DEFAULT_CSS = """
    LedgerView {
        border: tall $surface 80%;
    }
    """

    def __init__(self) -> None:
        super().__init__(zebra_stripes=True)
        self.cursor_type = "row"

    def on_mount(self) -> None:  # pragma: no cover - textual lifecycle
        self.add_columns("Date", "Description", "Amount", "Currency")

    def load_transactions(self, transactions: Iterable[TransactionDTO]) -> None:
        self.clear(columns=False)
        for txn in transactions:
            amount = sum(posting.amount for posting in txn.postings)
            currency = txn.postings[0].currency if txn.postings else "BRL"
            self.add_row(
                txn.date.strftime("%Y-%m-%d"),
                txn.description,
                f"{Decimal(amount):,.2f}",
                currency,
            )
