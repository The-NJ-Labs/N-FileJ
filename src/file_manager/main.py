import os
import sys
import subprocess
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree

class NFileJ(App):
    """A simple file manager app."""

    CSS_PATH = "main.tcss"

    # Removed "enter" from here because the Tree handles it internally
    BINDINGS = [
        ("^\\", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        # DirectoryTree handles its own navigation (Enter to expand/select)
        yield DirectoryTree(os.path.expanduser("~"), id="tree-container")
        yield Footer()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        file_path = event.path
        self.run_editor(str(file_path))

    def run_editor(self, file_path: str) -> None:
        with self.suspend():
            try:
                if sys.platform == "win32":
                    # use "shell=True" for Windows 'start' command
                    subprocess.run(f'start /wait "" "{file_path}"', shell=True)
                else:
                    editor = os.environ.get('EDITOR', 'nano')
                    subprocess.run([editor, file_path])
            except Exception as e:
                # This helps you see if the subprocess failed
                print(f"Error opening editor: {e}")

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-light" if self.theme == "textual-dark" else "textual-dark")

def main():
    app = NFileJ()
    app.run()

if __name__ == "__main__":
    main()