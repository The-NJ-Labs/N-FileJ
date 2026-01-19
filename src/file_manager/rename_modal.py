from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Button
from textual.containers import Grid

class RenameModal(ModalScreen[str]):
    def __init__(self, old_name: str):
        super().__init__()
        self.old_name = old_name

    def compose(self) -> ComposeResult:
        from textual.containers import Vertical, Horizontal
        with Vertical(id="modal_grid"):
            yield Label(f"✏️ Rename '{self.old_name}': Write the new name", id="label")
            yield Input(value=self.old_name, id="new_name_input")
            with Horizontal(id="button_row"):
                yield Button("Rename", variant="success", id="rename_btn")
                yield Button("Cancel", variant="error", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "rename_btn":
            self.dismiss(self.query_one(Input).value)
        else:
            self.dismiss(None)