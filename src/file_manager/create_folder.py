from textual.screen import ModalScreen
from textual.widgets import Input, Label, Button
from textual.containers import Grid
from textual.app import ComposeResult

class CreateFolderModal(ModalScreen[str]): # [str] means it returns a string
    """A pop-up to ask for a folder name."""

    def compose(self) -> ComposeResult:
        from textual.containers import Vertical, Horizontal
        with Vertical(id="modal_grid"):
            yield Label("Enter 📁folder name:", id="label")
            yield Input(placeholder="new_folder", id="folder_name")
            with Horizontal(id="button_row"):
                yield Button("Create", variant="success", id="create")
                yield Button("Cancel", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            name = self.query_one(Input).value
            self.dismiss(name)  # Close and send name back to main app
        else:
            self.dismiss(None)  # Cancel and send nothing back
