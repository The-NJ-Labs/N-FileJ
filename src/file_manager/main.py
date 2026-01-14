import os
import sys
import subprocess
from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree
if __package__ is None or __package__ == "":
    from create_folder import CreateFolderModal
    from rename_modal import RenameModal
else:
    from .create_folder import CreateFolderModal
    from .rename_modal import RenameModal

class NDirectoryTree(DirectoryTree):
    """Custom DirectoryTree that tracks double clicks and Enter key."""
    _should_open = False

    def on_click(self, event: events.Click) -> None:
        # Track if it was a double click, but don't interfere with internal logic
        self._should_open = (event.chain == 2)

    def on_key(self, event: events.Key) -> None:
        # Track if it was Enter, but don't interfere with internal logic
        self._should_open = (event.key == "enter")
class NFileJ(App):
    """A simple file manager app."""

    CSS_PATH = "main.tcss"

    # Removed "enter" from here because the Tree handles it internally
    BINDINGS = [
        ("alt+t", "toggle_dark", "Toggle mode(Dark/Light)"),
        ("q", "quit", "Quit"),
        ("alt+shift+n", "mkdir", "Create Folder"),
        ("delete", "delete", "Delete Folder/File"),
        ("f2", "rename", "Rename Folder/File")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        # Using custom NDirectoryTree for double-click support
        yield NDirectoryTree(os.path.expanduser("~"), id="tree-container")
        yield Footer()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        tree = self.query_one(NDirectoryTree)
        if getattr(tree, "_should_open", False):
            file_path = event.path
            self.run_editor(str(file_path))
            tree._should_open = False # Reset after opening

    def run_editor(self, file_path: str) -> None:
        with self.suspend():
            try:
                if sys.platform == "win32":
                    subprocess.run(f'start /wait "" "{file_path}"', shell=True)
                else:
                    editor = os.environ.get('EDITOR', 'nano')
                    subprocess.run([editor, file_path])
            except Exception as e:
                # This helps you see if the subprocess failed
                print(f"Error opening editor: {e}")

    def action_mkdir(self) -> None:
        tree = self.query_one(NDirectoryTree)
        
        # Determine the base directory for the new folder
        if tree.cursor_node and tree.cursor_node.data:
            base_path = tree.cursor_node.data.path
            if not base_path.is_dir():
                base_path = base_path.parent
        else:
            base_path = os.getcwd()

        def check_name(folder_name: str | None):
            if folder_name:
                new_path = os.path.join(base_path, folder_name)
                try:
                    os.makedirs(new_path, exist_ok=True)
                    tree.reload() # Refresh the tree
                    self.notify(f"Created: {folder_name}")
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        self.push_screen(CreateFolderModal(), check_name)

    def action_delete(self) -> None:
        tree = self.query_one(DirectoryTree)
        if tree.cursor_node and tree.cursor_node.data:
            file_path = tree.cursor_node.data.path
            try:
                if os.path.isdir(file_path):
                    os.rmdir(file_path)
                else:
                    os.remove(file_path)
                tree.reload() # Refresh the tree
                self.notify(f"Deleted: {file_path}")
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")    

    def action_rename(self) -> None:
        tree = self.query_one(DirectoryTree)
        if not tree.cursor_node or not tree.cursor_node.data:
            return

        old_path = tree.cursor_node.data.path
        old_name = old_path.name

        def perform_rename(new_name: str | None):
            if new_name and new_name != old_name:
                # Create the full new path
                new_path = old_path.with_name(new_name)
                
                try:
                    os.rename(old_path, new_path)
                    tree.reload() # Refresh the tree to show the change
                    self.notify(f"Renamed to {new_name}")
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        self.push_screen(RenameModal(old_name), perform_rename)      

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-light" if self.theme == "textual-dark" else "textual-dark")
    


def main():
    app = NFileJ()
    app.run()

if __name__ == "__main__":
    main()