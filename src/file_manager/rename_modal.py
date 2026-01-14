from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Button
from textual.containers import Grid

class RenameModal(ModalScreen[str]):
    def __init__(self, old_name: str):
        super().__init__()
        self.old_name = old_name

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(f"Renaming: {self.old_name}", id="label"),
            Input(value=self.old_name, id="new_name_input"),
            Button("Rename", variant="success", id="rename_btn"),
            Button("Cancel", variant="error", id="cancel_btn"),
            id="modal_grid"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "rename_btn":
            self.dismiss(self.query_one(Input).value)
        else:
            self.dismiss(None)