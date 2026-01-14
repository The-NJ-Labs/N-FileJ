import rich
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree, Static
from textual.containers import Container


class FileManager(App):
    """A simple file manager app."""

    CSS = """
    DirectoryTree {
        width: 100%;
        height: 100%;
        dock: top;
    }
    #content {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }
    """

    BINDINGS = [("^\\", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            DirectoryTree("~")
        )
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = ("textual-light" if self.theme == "textual-dark" else "textual-dark")


if __name__ == "__main__":
    app = FileManager()
    app.run()

