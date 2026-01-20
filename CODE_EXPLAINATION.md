# 📘 N-FileJ Absolute Code Dissection

This document provides an exhaustive, line-by-line explanation of the **N-FileJ** codebase. We will go through every single file and every single function.

**Recommendation:** Open this file on one side of your screen and the actual code in your editor on the other side.

---

## 📂 File: `src/file_manager/main.py`
This is the core application file. It sets up the window, the widgets, and handles all the user inputs (keyboard/mouse).

### Imports (Lines 1-7)
```python
import os
import sys
import subprocess
from pathlib import Path
from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, DirectoryTree
```
- **`import os`**: Standard Python library. Used for file operations like `os.rename`, `os.remove`, `os.makedirs`.
- **`import sys`**: Used here specifically to detect the Operating System (`sys.platform`) so we know how to open files.
- **`import subprocess`**: Allows running external commands. We use this to launch the text editor (like Notepad or Nano).
- **`from pathlib import Path`**: A modern way to handle file paths (e.g., `Path("folder") / "file.txt"`) instead of string manipulation.
- **`from textual...`**: Importing the necessary components from the Textual framework to build the TUI (Terminal User Interface).

### Package Handling (Lines 8-15)
```python
if __package__ is None or __package__ == "":
    from create_folder import CreateFolderModal
    from rename_modal import RenameModal
    from filtered_tree import FilteredDirectoryTree
else:
    from .create_folder import CreateFolderModal
    # ...
```
- **Why is this here?** This is a Python quirk.
- If you run `python src/file_manager/main.py`, Python thinks it's a standalone script, so it needs absolute imports (`from create_folder...`).
- If you run it as a module `python -m src.file_manager.main`, it needs relative imports (`from .create_folder...`).
- This block ensures the code runs without crashing no matter how you start it.

### Class Definition & Configuration (Lines 18-32)
```python
class NFileJ(App):
    """A simple file manager app."""
    CSS_PATH = "main.css"
    BINDINGS = [
        ("alt+t", "toggle_dark", "Toggle mode(Dark/Light)"),
        ("q", "quit", "Quit"),
        # ...
    ]
```
- **`class NFileJ(App)`**: Our app inherits from `App`. This gives it all the TUI superpowers.
- **`CSS_PATH = "main.tcss"`**: Tells Textual to load styling from the `main.tcss` file nearby.
- **`BINDINGS`**: A list of keyboard shortcuts.
    - `("q", "quit", "Quit")` means:
        - **Key**: Pressing `q`...
        - **Action**: ...calls the internal `action_quit` function (built-in to Textual)...
        - **Description**: ...and shows "Quit" in the footer.
    - Custom bindings like `("f2", "rename", ...)` look for a method named `action_rename` in this class.

### Application Lifecycle: `on_mount` (Lines 34-35)
```python
    def on_mount(self) -> None:
        self.query_one(FilteredDirectoryTree).focus()
```
- **`on_mount`**: This runs **once** right after the application starts up.
- **`self.query_one(FilteredDirectoryTree)`**: Searches the UI for the Directory Tree widget.
- **`.focus()`**: Forces the keyboard cursor into that widget. This means when the app opens, you can immediately start using Up/Down arrows to move through files without clicking first.

### UI Composition: `compose` (Lines 36-40)
```python
    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search files...", id="search-bar")
        yield FilteredDirectoryTree(Path("~").expanduser(), id="tree-container")
        yield Footer()
```
- **`compose`**: This constructs the visual layout.
- **`yield`**: Python keyword that returns "one item at a time".
- **`Header()`**: Adds the standard colored bar at the top/
- **`Input(...)`**: Creates a text box.
    - `id="search-bar"`: Gives it a name we can use to find it later in CSS or Python.
- **`FilteredDirectoryTree(...)`**:
    - `Path("~").expanduser()`: Gets the user's home directory (e.g., `C:\Users\Asus` or `/home/user`) as the starting point.
- **`Footer()`**: Adds the bar at the bottom that lists the keys defined in `BINDINGS`.

### Search Logic: Handling Input (Lines 42-44)
```python
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-bar":
            self.debounce_search(event.value)
```
- **`on_input_changed`**: This is an **Event Handler**. Textual calls this automatically whenever ANY character is typed into ANY input box.
- **`event.input.id == "search-bar"`**: We verify the typing happened in our search bar (not some other future input).
- **`event.value`**: The text currently inside the box.
- **`self.debounce_search`**: We pass the text to our helper function.

### Search Logic: Debouncing (Lines 46-50)
```python
    def debounce_search(self, value: str) -> None:
        """Debounce search to avoid lag."""
        if hasattr(self, "_search_timer"):
            self._search_timer.stop()
        self._search_timer = self.set_timer(0.3, lambda: self.perform_search(value))
```
- **Concept**: If you type "code", you type `c`, `o`, `d`, `e`. Without this, the app would search 4 times.
- **Line 48**: `if hasattr(self, "_search_timer")`: Checks if we already have a timer running (from the previous letter you typed).
- **Line 49**: `self._search_timer.stop()`: **CANCEL** that previous timer. We don't want to search for "cod" anymore, because you just typed "e".
- **Line 50**: `self.set_timer(0.3, ...)`: Start a NEW timer for 0.3 seconds.
    - If 0.3 seconds pass and you haven't typed anything else, it runs `self.perform_search(value)`.

### Search Logic: Executing (Lines 52-57)
```python
    def perform_search(self, value: str) -> None:
        try:
            tree = self.query_one(FilteredDirectoryTree)
            tree.update_filter(value)
        except Exception as e:
            self.notify(f"Search error: {e}", severity="error")
```
- **Line 54**: `self.query_one(...)`: Finds our custom tree widget instance.
- **Line 55**: `tree.update_filter(value)`: Calls the method inside `filtered_tree.py` (explained later) that actually hides/shows files.
- **Line 56-57**: Safety net. If something crashes during search, show a red error toast instead of crashing the whole app.

### Navigation Actions (Lines 59-63)
```python
    def action_focus_search(self) -> None:
        self.query_one(Input).focus()

    def action_focus_tree(self) -> None:
        self.query_one(FilteredDirectoryTree).focus()
```
- These correspond to key presses (defined in `BINDINGS`).
- `action_focus_search` (triggered by `/`): Jumps cursor to the Input box.
- `action_focus_tree` (triggered by `Escape`): Jumps cursor back to the file list.

### Opening Files (Lines 65-83)
```python
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        tree = self.query_one(FilteredDirectoryTree)
        if getattr(tree, "_should_open", False):
            file_path = event.path
            self.run_editor(str(file_path))
            tree._should_open = False # Reset after opening
```
- **Line 65**: Triggered when a file is "selected" (Enter or Click).
- **Line 67**: `getattr(tree, "_should_open", False)`:
    - This is a custom fix. In `filtered_tree.py`, we set `_should_open = True` ONLY if the user hit Enter or Double Clicked.
    - This prevents files from opening randomly when you just navigate with arrow keys.
- **Line 69**: Calls `run_editor`.
- **Line 70**: Resets variable to `False` so it doesn't open the next file automatically.

```python
    def run_editor(self, file_path: str) -> None:
        with self.suspend():
            try:
                if sys.platform == "win32":
                    subprocess.run(f'start /wait "" "{file_path}"', shell=True)
                else:
                    editor = os.environ.get('EDITOR', 'nano')
                    subprocess.run([editor, file_path])
            except ...
```
- **Line 73**: `with self.suspend()`: **Critical**. Textual takes over the terminal screen. If we run `nano` or `vim`, they ALSO need the screen. `suspend()` pauses Textual, clears the screen, lets the editor run, and then restores the Textual UI when the editor closes.
- **Line 75 (Windows)**: `start /wait "" "file"` tells Windows to open the file with its default program (e.g., VS Code, Notepad).
- **Line 78 (Linux/Mac)**: Tries to find your preferred editor var `$EDITOR`. If not found, defaults to `nano`.

### Creating Folders (Lines 84-106)
```python
    def action_mkdir(self) -> None:
        tree = self.query_one(FilteredDirectoryTree)
        
        # Determine the base directory
        if tree.cursor_node and tree.cursor_node.data:
            base_path = tree.cursor_node.data.path
            if not base_path.is_dir():
                base_path = base_path.parent
        else:
            base_path = os.getcwd()
```
- **Line 88**: Checks if the user has highlighted a row (`cursor_node`).
- **Line 90**: If I currently have a **File** selected (e.g., `main.py`), I can't create a folder inside a file. So `base_path.parent` switches the target to the folder *containing* that file.

```python
        def check_name(folder_name: str | None):
            if folder_name:
                new_path = os.path.join(base_path, folder_name)
                try:
                    os.makedirs(new_path, exist_ok=True)
                    tree.reload() # Refresh the tree
                    self.notify(f"Created: {folder_name}")
                except Exception as e: ...
```
- **`check_name`**: This is a **Closure** (a function inside a function). It will be passed to the Popup window.
- **Line 99**: `os.makedirs(..., exist_ok=True)`: Creates the folder. `exist_ok=True` means "don't crash if it already exists".
- **Line 100**: `tree.reload()`: Tells the UI to re-scan the disk so the new folder appears on screen.

```python
        self.push_screen(CreateFolderModal(), check_name)
```
- **Line 105**:
    1.  Creates the `CreateFolderModal` (the popup).
    2.  `push_screen` puts it on top of the main window.
    3.  Passes `check_name` as the function to call when the popup closes.

### Managing Files: Deleting (Lines 107-120)
```python
    def action_delete(self) -> None:
        # ...setup...
            try:
                if os.path.isdir(file_path):
                    os.rmdir(file_path)
                else:
                    os.remove(file_path)
                tree.reload()
                self.notify(f"Deleted: {file_path}")
```
- **Line 112**: Python has different commands for removing folders (`rmdir`) vs files (`remove`). We check which one it is using `isdir`.
- **Note**: `os.rmdir` only works on EMPTY folders. This is a safety feature so you don't accidentally delete your whole project.

### Managing Files: Renaming (Lines 121-141)
```python
    def action_rename(self) -> None:
        # Get current file info
        old_path = tree.cursor_node.data.path
        old_name = old_path.name

        def perform_rename(new_name: str | None):
            if new_name and new_name != old_name:
                new_path = old_path.with_name(new_name)
                try:
                    os.rename(old_path, new_path)
                    tree.reload()
        
        self.push_screen(RenameModal(old_name), perform_rename)
```
- **Line 132**: `old_path.with_name(new_name)`.
    - Example: If `old_path` is `C:/Docs/foo.txt` and `new_name` is `bar.txt`.
    - `with_name` magically creates `C:/Docs/bar.txt`.
- **Line 141**: `RenameModal(old_name)`. We pass the current filename to the popup so the input box isn't empty (it lets the user edit the existing name).

---

## 🌲 File: `src/file_manager/filtered_tree.py`

This file overrides the standard `DirectoryTree` widget to make it searchable.

### Class Setup (Lines 6-8)
```python
class FilteredDirectoryTree(DirectoryTree):
    search_term: str = ""
    _should_open: bool = False
```
- **`search_term`**: Defines a new variable to hold what the user typed.
- **`_should_open`**: A custom flag we invented to track if the user *really* wants to open a file.

### Input Event Overrides (Lines 14-25)
```python
    def on_click(self, event: events.Click) -> None:
        if event.button == 1:
            if event.chain == 2:
                self._should_open = True
            else:
                self._should_open = False
```
- **`on_click`**: Runs on mouse click.
- **Line 16**: `event.chain == 2`. This means "Double Click".
- **Logic**: If double click -> Open file (`True`). If single click -> Just highlight (`False`).

```python
    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self._should_open = True
        else:
            self._should_open = False
```
- **`on_key`**: Runs on keyboard press.
- **Logic**: Only the `enter` key sets the Open flag to `True`. Arrow keys set it `False`.

### The Core Search Algorithm: `filter_paths` (Lines 27-76)
This method is called automatically by Textual whenever it lists files in a folder. We override it.

```python
    def filter_paths(self, paths: list[Path]) -> list[Path]:
        if not self.search_term:
            return paths
```
- **Line 28**: If search box is empty, return the list untouched.

```python
        def contains_match(path: Path, depth: int) -> bool:
            if depth <= 0: return False
            if path in self._search_cache: return self._search_cache[path]
            # ...
```
- **Line 39**: **Recursive Function**. This helper checks if a folder contains the search term *deep inside it*.
- **Line 40**: `depth <= 0`: Stops infinite recursion. We limit look-ahead to 3 levels.
- **Line 42**: **Caching**. If we already checked this folder in this search session, return the answer instantly.

```python
            try:
                with os.scandir(path) as it:
                    for entry in it:
                        # Direct match in this folder
                        if self.search_term in entry.name.lower():
                            self._search_cache[path] = True
                            return True
```
- **Line 46**: `os.scandir(path)`. Extremely fast way to list files.
- **Line 49**: Checks if current file matches. If yes, the `path` (the parent folder) is valid.

```python
                        # Recursive check for sub-folders
                        if entry.is_dir():
                            # Skip huge binary/meta folders
                            if entry.name in (".git", "node_modules", ...):
                                continue
                            if contains_match(Path(entry.path), depth - 1):
                                self._search_cache[path] = True
                                return True
```
- **Lines 55-56**: **Optimization**. Prevents searching massive folders that would freeze the app.
- **Line 57**: `contains_match(..., depth - 1)`. Calls itself! It drills down one level deeper.

### Applying the Filter (Lines 66-76)
```python
        filtered = []
        for p in paths:
            # Case 1: The item itself matches
            if self.search_term in p.name.lower():
                filtered.append(p)
            # Case 2: It's a folder, show it if it contains something useful
            elif p.is_dir():
                if contains_match(p, depth=3):
                    filtered.append(p)
                    
        return filtered
```
- This part runs for every item in the current view.
- It builds a `filtered` list containing ONLY the items that match our rules.

---

## 🆕 File: `src/file_manager/create_folder.py`

### Definition (Lines 6-23)
```python
class CreateFolderModal(ModalScreen[str]):
```
- **`[str]`**: Uses Python Generics. It tells the type checker "this Modal, when closed, produces a string".

```python
    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Enter folder name:", id="label"),
            Input(placeholder="new_folder", id="folder_name"),
            Button("Create", variant="success", id="create"),
            Button("Cancel", variant="error", id="cancel"),
            id="modal_grid",
        )
```
- **`Grid`**: A container that places items in a grid/table layout (defined in CSS).
- **`Input`**: Where the user types.
- **`Button`**:
    - `variant="success"`: Makes it Green.
    - `variant="error"`: Makes it Red.

```python
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            name = self.query_one(Input).value
            self.dismiss(name)  # Returns the name
        else:
            self.dismiss(None)  # Returns nothing
```
- **`self.dismiss(value)`**: This method CLOSES the modal. The `value` you pass here is what ends up in the `check_name` callback in `main.py`.

---

## 🎨 File: `src/file_manager/main.tcss`
This is pure CSS (Cascading Style Sheets) adapted for the terminal.

### Layout for Modal (Lines 24-35)
```css
#modal_grid {
    grid-size: 2;                 /* 2 columns wide */
    grid-rows: auto auto auto;    /* 3 rows, height adjusts to content */
    grid-gutter: 1;               /* Space between cells */
    padding: 1 2;                 /* Inner spacing */
    width: 60;                    /* Fixed width (characters) */
    background: $surface;         /* Theme color */
    border: thick $primary;       /* thick line border around modal */
}
```

### Component Specifics (Lines 37-54)
```css
#label {
    column-span: 2; /* Span across both columns */
    ...
}

#folder_name {
    column-span: 2; /* Input box spans full width */
    ...
}

#create, #cancel {
    width: 100%;    /* Buttons only take 1 column each, so fill that column */
}
```
- **Explanation**:
    - Row 1: Label (takes 2 cells)
    - Row 2: Input (takes 2 cells)
    - Row 3: Create Button (Cell 1), Cancel Button (Cell 2)
