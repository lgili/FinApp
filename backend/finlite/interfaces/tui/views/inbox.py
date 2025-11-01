"""Inbox view for statement entries."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from textual.widgets import DataTable

from ..services import StatementEntryRow


class InboxView(DataTable):
    """Table listing pending statement entries."""

    DEFAULT_CSS = """
    InboxView {
        border: tall $surface 80%;
    }
    """

    def __init__(self) -> None:
        super().__init__(zebra_stripes=True)
        self.cursor_type = "row"
        self._rows: dict[int, StatementEntryRow] = {}

    def on_mount(self) -> None:  # pragma: no cover - textual lifecycle
        self.clear()
        self.add_columns("Date", "Description", "Amount", "Currency", "Suggested")

    def load_entries(self, entries: list[StatementEntryRow]) -> None:
        self.clear(columns=False)
        self._rows.clear()
        for idx, entry in enumerate(entries):
            self._rows[idx] = entry
            self.add_row(
                entry.occurred_at.strftime("%Y-%m-%d"),
                entry.memo,
                f"{entry.amount:,.2f}",
                entry.currency,
                entry.suggested_account or "-",
            )
        if entries:
            self.cursor_coordinate = (0, 0)

    def get_selected_entry(self) -> StatementEntryRow | None:
        if not self.row_count or self.cursor_row is None:
            return None
        return self._rows.get(self.cursor_row)
