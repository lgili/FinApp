"""Accounts view for TUI."""

from __future__ import annotations

from textual.widgets import DataTable


class AccountsView(DataTable):
    """Displays accounts and account types."""

    DEFAULT_CSS = """
    AccountsView {
        border: tall $surface 80%;
    }
    """

    def __init__(self) -> None:
        super().__init__(zebra_stripes=True)
        self.cursor_type = "row"

    def on_mount(self) -> None:  # pragma: no cover - textual lifecycle
        self.add_columns("Code", "Type")

    def load_accounts(self, accounts: list[tuple[str, str]]) -> None:
        self.clear(columns=False)
        for code, account_type in accounts:
            self.add_row(code, account_type)
