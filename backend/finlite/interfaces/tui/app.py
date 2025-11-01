"""Finlite Textual user interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from rapidfuzz import process
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from .services import (
    DashboardSummary,
    get_accounts_tree,
    get_dashboard_summary,
    get_pending_entries,
    post_statement_entries,
)
from .views.accounts import AccountsView
from .views.dashboard import DashboardView
from .views.inbox import InboxView
from .views.ledger import LedgerView
from .views.placeholders import PlaceholderView
from .views.reports import ReportsView


NAV_ITEMS = [
    ("dashboard", "Dashboard"),
    ("inbox", "Inbox"),
    ("ledger", "Ledger"),
    ("accounts", "Accounts"),
    ("reports", "Reports"),
    ("rules", "Rules"),
]


@dataclass
class PaletteCommand:
    label: str
    action: str
    description: str = ""


class PaletteCommandSelected(Message):
    """Message emitted when a command is chosen from the palette."""

    def __init__(self, command: PaletteCommand) -> None:
        self.command = command
        super().__init__()


class InboxFilterSubmitted(Message):
    """Message emitted when a new inbox filter is provided."""

    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class CommandPalette(ModalScreen[None]):
    """Simple command palette using fuzzy search."""

    BINDINGS = [Binding("escape", "close", "Close")]

    def __init__(self, commands: list[PaletteCommand]) -> None:
        super().__init__()
        self._commands = commands
        self._list = ListView()
        self._input = Input(placeholder="Type a command…")

    def compose(self) -> ComposeResult:  # pragma: no cover - UI layout
        yield Container(
            Static("Command Palette", classes="palette-title"),
            self._input,
            self._list,
            classes="palette",
        )

    def on_mount(self) -> None:  # pragma: no cover - UI lifecycle
        self._input.focus()
        self._rebuild("")

    @on(Input.Changed)
    def filter_commands(self, event: Input.Changed) -> None:
        self._rebuild(event.value)

    @on(Input.Submitted)
    def accept_first(self, event: Input.Submitted) -> None:
        if self._list.children:
            item = self._list.children[0]
            command = item.data.get("command") if isinstance(item, ListItem) else None
            if command:
                self._trigger(command)
        self.app.pop_screen()

    @on(ListView.Selected)
    def on_list_selected(self, event: ListView.Selected) -> None:
        command = event.item.data.get("command")
        if command:
            self._trigger(command)
        self.app.pop_screen()

    def _rebuild(self, query: str) -> None:
        self._list.clear()
        if not query:
            matches = [(cmd, 100) for cmd in self._commands[:7]]
        else:
            matches = process.extract(
                query,
                [cmd.label for cmd in self._commands],
                limit=7,
            )
            matches = [
                (self._commands[i], score)
                for (label, score, i) in matches  # type: ignore[misc]
            ]
        for command, score in matches:
            item = ListItem(Label(f"{command.label}"), Label(command.description or ""))
            item.data = {"command": command}
            self._list.append(item)

    def _trigger(self, command: PaletteCommand) -> None:
        self.app.post_message(PaletteCommandSelected(command))


class FilterPrompt(ModalScreen[None]):
    """Simple modal to capture filter text."""

    BINDINGS = [Binding("escape", "close", "Close")]

    def __init__(self, initial: str = "") -> None:
        super().__init__()
        self._input = Input(value=initial, placeholder="Filter inbox (press Enter to apply)")

    def compose(self) -> ComposeResult:  # pragma: no cover - UI layout
        yield Container(
            Static("Inbox Filter", classes="palette-title"),
            self._input,
            classes="palette",
        )

    def on_mount(self) -> None:  # pragma: no cover
        self._input.focus()

    @on(Input.Submitted)
    def submit(self, event: Input.Submitted) -> None:
        self.app.post_message(InboxFilterSubmitted(event.value))
        self.app.pop_screen()

class NavigationSidebar(ListView):
    """List-based navigation sidebar."""

    def __init__(self) -> None:
        items = [ListItem(Label(label), id=key) for key, label in NAV_ITEMS]
        super().__init__(*items, id="nav")
        self.cursor_type = "row"


class FinliteTUI(App[None]):
    """Main Textual application."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
    }

    #body {
        layout: horizontal;
    }

    #sidebar {
        width: 28;
        background: $surface 85%;
        border: hkey $boost;
        padding: 1 0;
    }

    #content {
        width: 1fr;
        background: $background;
    }

    .palette {
        width: 60%;
        margin: 1 2;
        padding: 1;
        background: $surface 98%;
        border: round $boost;
    }

    .palette-title {
        text-style: bold;
        padding-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+k", "command_palette", "Command Palette"),
        Binding("ctrl+r", "refresh_view", "Refresh"),
    ]

    def __init__(self, container, **kwargs) -> None:
        super().__init__(**kwargs)
        self._container = container
        self._nav: NavigationSidebar | None = None
        self._content: Container | None = None
        self._views: dict[str, Static] = {}
        self._active_view: str = "dashboard"
        self._inbox_filter: str = ""

    def compose(self) -> ComposeResult:  # pragma: no cover - UI layout
        yield Header(show_clock=True)
        with Container(id="body"):
            with Vertical(id="sidebar"):
                yield Static("FINLITE", classes="logo")
                self._nav = NavigationSidebar()
                yield self._nav
            self._content = Container(id="content")
            yield self._content
        yield Footer()

    def on_mount(self) -> None:  # pragma: no cover - UI lifecycle
        self._ensure_view("dashboard")
        self._ensure_view("inbox")
        self._ensure_view("ledger")
        self._ensure_view("accounts")
        self._ensure_view("reports")
        self._ensure_view("rules")
        self.switch_view("dashboard")

    def _ensure_view(self, name: str) -> None:
        if name in self._views:
            return
        if not self._content:
            return
        if name == "dashboard":
            widget: Static = DashboardView()
        elif name == "inbox":
            widget = InboxView()
        elif name == "ledger":
            widget = LedgerView()
        elif name == "accounts":
            widget = AccountsView()
        elif name == "reports":
            widget = ReportsView()
        else:
            widget = PlaceholderView("Rules management view coming soon.")
        widget.display = False
        self._views[name] = widget
        self._content.mount(widget)

    def action_switch_view(self, name: str) -> None:
        self.switch_view(name)

    def switch_view(self, name: str) -> None:
        if name not in self._views:
            return
        for key, view in self._views.items():
            view.display = key == name
        if self._nav:
            index = next((i for i, (key, _) in enumerate(NAV_ITEMS) if key == name), 0)
            self._nav.index = index
        self._active_view = name
        self.refresh_view()

    def action_refresh_view(self) -> None:
        self.refresh_view()

    def refresh_view(self) -> None:
        if self._active_view == "dashboard":
            summary = get_dashboard_summary(self._container)
            view: DashboardView = self._views["dashboard"]  # type: ignore[assignment]
            view.show_summary(summary)
        elif self._active_view == "inbox":
            rows = get_pending_entries(self._container, search=self._inbox_filter or None)
            view: InboxView = self._views["inbox"]  # type: ignore[assignment]
            view.load_entries(rows)
        elif self._active_view == "accounts":
            accounts = get_accounts_tree(self._container)
            view: AccountsView = self._views["accounts"]  # type: ignore[assignment]
            view.load_accounts(accounts)
        elif self._active_view == "ledger":
            transactions_uc = self._container.list_transactions_use_case()
            transactions = transactions_uc.execute()
            view: LedgerView = self._views["ledger"]  # type: ignore[assignment]
            view.load_transactions(transactions)
        elif self._active_view == "reports":
            view: ReportsView = self._views["reports"]  # type: ignore[assignment]
            view.show_cashflow(self._container)

    async def action_command_palette(self) -> None:
        commands = [
            PaletteCommand("Open Dashboard", "switch:dashboard"),
            PaletteCommand("Open Inbox", "switch:inbox"),
            PaletteCommand("Post selected inbox entry", "inbox:post", "Shortcut A"),
            PaletteCommand("Filter inbox", "inbox:filter"),
            PaletteCommand("Generate cashflow report", "reports:cashflow"),
            PaletteCommand("Refresh view", "refresh"),
        ]
        self.push_screen(CommandPalette(commands))

    @on(PaletteCommandSelected)
    async def handle_palette_selection(self, event: PaletteCommandSelected) -> None:
        command = event.command
        if command.action.startswith("switch:"):
            _, view_name = command.action.split(":", 1)
            self.switch_view(view_name)
        elif command.action == "inbox:post":
            await self._post_selected_entry()
        elif command.action == "inbox:filter":
            await self._prompt_inbox_filter()
        elif command.action == "reports:cashflow":
            self.switch_view("reports")
        elif command.action == "refresh":
            self.refresh_view()

    async def _post_selected_entry(self) -> None:
        if self._active_view != "inbox":
            self.switch_view("inbox")
        view: InboxView = self._views["inbox"]  # type: ignore[assignment]
        entry = view.get_selected_entry()
        if not entry:
            self.notify("Select an entry first", severity="warning")
            return
        post_statement_entries(self._container, [entry.id])
        self.notify("Entry posted", severity="information")
        self.refresh_view()

    async def _prompt_inbox_filter(self) -> None:
        self.push_screen(FilterPrompt(self._inbox_filter))

    async def on_key(self, event: Key) -> None:  # pragma: no cover - input handling
        if event.key == "/":
            await self._prompt_inbox_filter()
            return
        if event.key in {"1", "2", "3", "4", "5", "6"}:
            idx = int(event.key) - 1
            if 0 <= idx < len(NAV_ITEMS):
                self.switch_view(NAV_ITEMS[idx][0])
            return
        if self._active_view == "inbox" and event.key.lower() == "a":
            await self._post_selected_entry()

    @on(InboxFilterSubmitted)
    def on_filter_submitted(self, event: InboxFilterSubmitted) -> None:
        self._inbox_filter = event.text or ""
        self.switch_view("inbox")


def run_tui(container) -> None:
    """Entry point used by the CLI."""
    app = FinliteTUI(container)
    app.run()
