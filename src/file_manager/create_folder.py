from textual.screen import ModalScreen
from textual.widgets import Input, Label, Button
from textual.containers import Grid
from textual.app import ComposeResult

class CreateFolderModal(ModalScreen[str]): # [str] means it returns a string
    """A pop-up to ask for a folder name."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Enter folder name:", id="label"),
            Input(placeholder="new_folder", id="folder_name"),
            Button("Create", variant="success", id="create"),
            Button("Cancel", variant="error", id="cancel"),
            id="modal_grid",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            name = self.query_one(Input).value
            self.dismiss(name)  # Close and send name back to main app
        else:
            self.dismiss(None)  # Cancel and send nothing back
