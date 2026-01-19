import os
import sys
import subprocess
import pyperclip
from pathlib import Path
from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, DirectoryTree
if __package__ is None or __package__ == "":
    from create_folder import CreateFolderModal
    from rename_modal import RenameModal
    from filtered_tree import FilteredDirectoryTree
else:
    from .create_folder import CreateFolderModal
    from .rename_modal import RenameModal
    from .filtered_tree import FilteredDirectoryTree


class NFileJ(App):
    """A simple file manager app."""

    CSS_PATH = "main.tcss"

    # Removed "enter" from here because the Tree handles it internally
    BINDINGS = [
        ("alt+t", "toggle_dark", "Toggle mode(Dark/Light)"),
        ("q", "quit", "Quit"),
        ("alt+shift+n", "mkdir", "Create Folder"),
        ("delete", "delete", "Delete Folder/File"),
        ("f2", "rename", "Rename Folder/File"),
        ("/", "focus_search", "Search"),
        ("escape", "focus_tree", "Back to Tree"),
        ("alt+shift+c", "get_path", "Get File/Folder Path"),
    ]

    def on_mount(self) -> None:
        self.query_one(FilteredDirectoryTree).focus()
    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search files...", id="search-bar") # New Search Bar
        yield FilteredDirectoryTree(Path("~").expanduser(), id="tree-container")
        yield Footer()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-bar":
            self.debounce_search(event.value)

    def debounce_search(self, value: str) -> None:
        """Debounce search to avoid lag."""
        if hasattr(self, "_search_timer"):
            self._search_timer.stop()
        self._search_timer = self.set_timer(0.3, lambda: self.perform_search(value))

    def perform_search(self, value: str) -> None:
        try:
            tree = self.query_one(FilteredDirectoryTree)
            tree.update_filter(value)
        except Exception as e:
            self.notify(f"Search error: {e}", severity="error")
    
    def action_focus_search(self) -> None:
        self.query_one(Input).focus()

    def action_focus_tree(self) -> None:
        self.query_one(FilteredDirectoryTree).focus()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        tree = self.query_one(FilteredDirectoryTree)
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
        tree = self.query_one(FilteredDirectoryTree)
        
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
        tree = self.query_one(FilteredDirectoryTree)
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
        tree = self.query_one(FilteredDirectoryTree)
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

    def action_get_path(self) -> None:
        tree = self.query_one(FilteredDirectoryTree)
        if tree.cursor_node and tree.cursor_node.data:
            path = str(tree.cursor_node.data.path)
            pyperclip.copy(path)
            self.notify(f"Copied path to clipboard!")

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-light" if self.theme == "textual-dark" else "textual-dark")
    


def main():
    app = NFileJ()
    app.run()

if __name__ == "__main__":
    main()