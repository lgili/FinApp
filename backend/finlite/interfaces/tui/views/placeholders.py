"""Placeholder views used for sections not yet fully implemented."""

from textual.widgets import Static


class PlaceholderView(Static):
    """Simple placeholder view showing a message."""

    DEFAULT_CSS = """
    PlaceholderView {
        padding: 2;
        text-style: italic;
        color: $text 70%;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
