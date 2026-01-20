import os
import sys
import shutil
import subprocess
import pyperclip
import re
from pathlib import Path
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Input, Static, DirectoryTree
from rich.text import Text
from rich.markup import escape
if __package__ is None or __package__ == "":
    from create_folder import CreateFolderModal
    from rename_modal import RenameModal
    from filtered_tree import FilteredDirectoryTree
else:
    from .create_folder import CreateFolderModal
    from .rename_modal import RenameModal
    from .filtered_tree import FilteredDirectoryTree


class MultilineFooter(Static):
    def on_mount(self) -> None:
        self.update_content()
        # Refresh whenever focus changes to update binding context
        self.watch(self.app, "focused", self.update_content)

    def on_resize(self, event: events.Resize) -> None:
        self.update_content()

    def update_content(self, *args, **kwargs) -> None:
        parts = []
        # Access the BINDINGS from the App class
        app_bindings = getattr(self.app, "BINDINGS", [])
        
        for binding in app_bindings:
            # Handle both tuples and Binding objects safely
            if isinstance(binding, tuple):
                key, action, description = binding
            else:
                key = getattr(binding, "key", "")
                action = getattr(binding, "action", "")
                description = getattr(binding, "description", "")

            # Use Textual markup for the whole thing to ensure links work
            # We explicitly set NO underline to keep the look clean
            # Adding a bit more padding around the items
            part = f"[bold reverse] {escape(key.upper())} [/] [@click=app.{action}]{escape(description)}[/]"
            parts.append(part)
        
        self.update("    ".join(parts))


class NFileJ(App):
    """A simple file manager app."""

    CSS_PATH = "main.css"

    # Removed "enter" from here because the Tree handles it internally
    BINDINGS = [
        ("/", "focus_search", "Search"),
        ("escape", "focus_tree", "Tree"),
        ("alt+shift+n", "mkdir", "New Folder"),
        ("ctrl+c", "copy", "Copy"),
        ("ctrl+x", "cut", "Cut"),
        ("ctrl+v", "paste", "Paste"),
        ("f2", "rename", "Rename"),
        ("alt+shift+c", "get_path", "Copy Path"),
        ("delete", "delete", "Delete"),
        ("alt+t", "toggle_dark", "Dark/Light"),
        ("q", "quit", "Quit"),
    ]

    source_path: Path | None = None
    is_cut: bool = False

    def on_mount(self) -> None:
        self.source_path: Path | None = None
        self.query_one(FilteredDirectoryTree).focus()
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="search-container"):
            yield Static("🔎", id="search-icon")
            yield Input(placeholder="Search files...", id="search-bar")
        yield FilteredDirectoryTree(Path("~").expanduser(), id="tree-container")
        yield MultilineFooter()

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

    def action_copy(self, path: Path | None = None) -> None:
        self.is_cut = False
        tree = self.query_one(FilteredDirectoryTree)
        if tree.cursor_node and tree.cursor_node.data:
            self.source_path = tree.cursor_node.data.path
            self.notify(f"Copied: {self.source_path.name}")
            
    def action_cut(self, path: Path | None = None) -> None:
        self.is_cut = True
        tree = self.query_one(FilteredDirectoryTree)
        if tree.cursor_node and tree.cursor_node.data:
            self.source_path = tree.cursor_node.data.path
            self.notify(f"Cut: {self.source_path.name}")

    def action_paste(self) -> None:
        tree = self.query_one(FilteredDirectoryTree)
        if not self.source_path or not self.source_path.exists():
            self.notify("Nothing to Paste or Source Missing!", severity="error")
            return
        
        # 1. Figure out WHERE we are pasting
        target_node = tree.cursor_node
        if target_node and target_node.data:
            target_path = target_node.data.path
            base_dir = target_path if target_path.is_dir() else target_path.parent
        else:
            base_dir = Path.cwd()

        # 2. Smart Naming Logic (Prevents the (1)(1)(1) nightmare)
        stem = self.source_path.stem
        suffix = self.source_path.suffix
        
        clean_stem = re.sub(r'\s\(\d+\)$', '', stem)
        
        new_path = base_dir / f"{clean_stem}{suffix}"
        counter = 1
        
        # Keep incrementing until we find a name that DOES NOT exist
        while new_path.exists():
            new_path = base_dir / f"{clean_stem} ({counter}){suffix}"
            counter += 1

        # 3. The Actual Move/Copy
        try:
            if self.is_cut:
                # SHIFT+DELETE logic: shutil.move is the correct way to 'Cut'
                # It handles the move and the deletion of the source in one atomic step
                shutil.move(str(self.source_path), str(new_path))
                self.source_path = None # Clear clipboard after move
                self.notify(f"Moved to: {new_path.name}")
            else:
                # Standard Copy
                if self.source_path.is_dir():
                    shutil.copytree(self.source_path, new_path)
                else:
                    shutil.copy2(self.source_path, new_path)
                self.notify(f"Pasted: {new_path.name}")
            
            tree.reload()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            
    def action_delete(self, path: Path | None = None) -> None:
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