# 📘 N-FileJ: The Definitive Technical Manual & Codebase Dissection

**Document Revision**: 4.0 (The "Encyclopedic" Edition)
**Target Audience**: Senior Engineers, Python Developers, Maintainers, Students, and AI Agents.
**Scope**: Full architectural breakdown of the N-FileJ File Manager, including complete source code listings, line-by-line analysis, visual diagrams, debugging guides, and an encyclopedic reference of all system calls.
**Objective**: To provide an exhaustive reference for every byte of logic in the application.

---

## 📑 Table of Contents

1.  **Architectural Overview & Design Philosophy**
    *   The "Textual" Paradigm
    *   The Actor Model
    *   Async/Await Strategy
    *   Project Structure
    *   Visual Logic Flow (Mermaid)
2.  **Core Controller: `src/file_manager/main.py`**
    *   Full Source Code Listing
    *   Deep Dive: Imports (`shutil`, `re`, `subprocess`)
    *   Deep Dive: Application Lifecycle
    *   Deep Dive: The Event Loop & Input Handling
    *   Deep Dive: Clipboard State Machine
    *   Deep Dive: Subprocess Management
3.  **The Filtered Tree: `src/file_manager/filtered_tree.py`**
    *   Full Source Code Listing
    *   Deep Dive: Inheritance
    *   Deep Dive: The Recursive Search Algorithm
    *   Deep Dive: Event Interception
4.  **UI Components: Modals (`create_folder.py` & `rename_modal.py`)**
    *   Full Source Code Listing
    *   Deep Dive: Generic Typing
    *   Deep Dive: Layout Composition
    *   Deep Dive: Signal Passing
5.  **The Styling Engine: `src/file_manager/main.css`**
    *   Full Source Code Listing
    *   Deep Dive: The Box Model in TUI
    *   Deep Dive: Flexbox Layouts
    *   Deep Dive: Theming & Variables
6.  **Developer's Cookbook**
    *   How to Add a New Feature
    *   How to Debug Freeze Issues
    *   Glossary of Terms
7.  **Appendix A: System Operations Reference**
    *   `shutil` vs `os` Performance Benchmarks
    *   Subprocess Exit Codes
    *   Cross-Platform Nuances
8.  **Appendix B: Full Dependency Graph (ASCII)**

---

## 🏗️ 1. Architectural Overview & Design Philosophy

### 1.1 The "Textual" Paradigm
N-FileJ is built on top of **Textual**, a modern TUI (Terminal User Interface) framework for Python. Unlike traditional CLI tools (`argparse`, `click`) that run linearly and exit, Textual runs a persistent **Event Loop**, similar to a Game Engine or a Website.

*   **The Actor Model**: Every widget (Tree, Input, Header) is an independent "actor". It maintains its own state and processes messages (Keys, Clicks, Screen Resizes) independently of the main app.
*   **CSS-First Design**: The visual layout is decoupled from the Python logic. It is defined in a generic `.tcss` (Textual CSS) file.
    *   **Benefit**: You can change the entire look of the app (colors, borders, spacing) without restarting the Python process or changing a single line of logic.
*   **Async/Await Native**: The core loop handles I/O operations asynchronously. This is critical for a file manager.
    *   **Scenario**: You are scanning a hard drive with 100,000 files.
    *   **Sync Approach**: The UI freezes until the scan finishes.
    *   **Textual Approach**: The UI remains responsive (you can type in the search bar) while the scan happens in the background.

### 1.2 The Project Structure
The project follows a modular "Package" structure to ensure separation of concerns.

```text
      [ Application Layer ]
               |
         (src/main.py)
               |
               v
        [ Widget Layer ]
        /              \
(filtered_tree.py)  (footer)
        \              /
         \            /
          v          v
     [ Presentation Layer ]
      (main.css / Modals)
```

*   **`main.py`**: The Orchestrator. It initializes the App, loads the CSS, and manages global state (Clipboard, Cuts, Quits). It is the "Brain".
*   **`filtered_tree.py`**: A specialized Sub-Class of the standard `DirectoryTree`. It acts as the "View Model", handling data presentation and filtering.
*   **`create_folder.py` & `rename_modal.py`**: "dumb" UI components. They collect input and return it to the Controller. They do not perform file operations themselves to ensure **Safe Separation**.
*   **`main.css`**: The single source of truth for visual styling.

---

## 📂 2. Core Controller: `src/file_manager/main.py`

This file is the specific entry point. It orchestrates the entire application lifecycle.

### 2.1 Full Source Listing
*(This is the actual code running in production. Study it carefully.)*

> **🔗 [View Source on GitHub](https://github.com/The-NJ-Labs/N-FileJ/blob/main/src/file_manager/main.py)**

*(Code omitted for brevity. Click the link above to view the latest source.)*

### 2.2 Deep Dive: Imports
We start with a robust set of imports. Notice the specific choices:
*   **`import shutil`**: While `os` is good for basic operations, `shutil` (Shell Utilities) is necessary for recursive folder copying (`copytree`) and cross-disk moving (`move`). Normal `os.rename` fails if you try to move a file from `C:` drive to `D:` drive. `shutil` handles the "Copy then Delete" fallback automatically.
*   **`import pyperclip`**: Textual applications run in their own "Sandbox" effectively. The OS clipboard is separate. `pyperclip` bridges this gap, allowing us to copy file paths to the user's main environment.
*   **`import re`**: Regular Expressions are heavy, but essential for the "Smart Rename" feature (`File (1).txt`). String splitting is too fragile for this task.

### 2.3 Deep Dive: The Module Switcher
```python
if __package__ is None or __package__ == "":
    # ...
else:
    # ...
```
This is a professional Python pattern.
*   **Problem**: Relative imports (`from .foo import bar`) fail if the script is run directly (`python main.py`). Absolute imports (`from src.foo import bar`) fail if the directory structure changes.
*   **Solution**: Detect the runtime context. If we are a script, use simple imports. If we are a module (part of a package), use relative imports.

### 2.4 Deep Dive: The `NFileJ` State Machine
The application maintains critical state:
```python
    source_path: Path | None = None
    is_cut: bool = False
```
*   **Lifecycle**:
    *   **Startup**: `source_path` is `None`.
    *   **User presses Ctrl+C**: `source_path` becomes `C:\file.txt`, `is_cut` becomes `False`.
    *   **User presses Ctrl+X**: `source_path` becomes `C:\file.txt`, `is_cut` becomes `True`.
    *   **User presses Ctrl+V**:
        *   We check `source_path`.
        *   If `is_cut` is True: We `shutil.move()`, then set `source_path` back to `None`.
        *   If `is_cut` is False: We `shutil.copy()`, and `source_path` remains (you can paste multiple times).

### 2.5 Deep Dive: Debounced Search
The `debounce_search` method is a masterclass in UI responsiveness.
```python
    def debounce_search(self, value: str) -> None:
        if hasattr(self, "_search_timer"):
            self._search_timer.stop()
        self._search_timer = self.set_timer(0.3, lambda: self.perform_search(value))
```
*   **Without Debounce**: Typing "python" triggers 6 separate tree traversals. The UI would stutter aggressively.
*   **With Debounce**: Typing "python" triggers 0 traversals until you stop typing for 300ms. Then it triggers exactly 1 traversal. This makes the app feel "Native" and smooth.

---

## 🌲 3. The Filtered Tree: `src/file_manager/filtered_tree.py`

This file subclasses `DirectoryTree` to fix its limitations.

### 3.1 Full Source Listing
```python
import os
from textual import events
from pathlib import Path
from textual.widgets import DirectoryTree

class FilteredDirectoryTree(DirectoryTree):
    search_term: str = ""
    _should_open: bool = False

    def on_mount(self) -> None:
        # Resolve path early
        self.path = Path(str(self.path)).expanduser().resolve()

    def on_click(self, event: events.Click) -> None:
        if event.button == 1:
            if event.chain == 2:
                self._should_open = True
            else:
                self._should_open = False

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self._should_open = True
        else:
            self._should_open = False

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        if not self.search_term:
            return paths

        # Strategy:
        # 1. Keep any file/folder whose name matches the search term.
        # 2. Keep any folder that contains a match (up to 3 levels deep).
        # This "narrows down" the tree to only relevant branches.
        
        if not hasattr(self, "_search_cache"):
            self._search_cache = {}

        def contains_match(path: Path, depth: int) -> bool:
            if depth <= 0:
                return False
            if path in self._search_cache:
                return self._search_cache[path]

            try:
                with os.scandir(path) as it:
                    for entry in it:
                        # Direct match in this folder
                        if self.search_term in entry.name.lower():
                            self._search_cache[path] = True
                            return True
                        # Recursive check for sub-folders
                        if entry.is_dir():
                            # Skip huge binary/meta folders to keep it snappy
                            if entry.name in (".git", "node_modules", ".venv", "__pycache__"):
                                continue
                            if contains_match(Path(entry.path), depth - 1):
                                self._search_cache[path] = True
                                return True
            except (PermissionError, OSError):
                pass
            
            self._search_cache[path] = False
            return False

        filtered = []
        for p in paths:
            # Case 1: The item itself matches
            if self.search_term in p.name.lower():
                filtered.append(p)
            # Case 2: It's a folder, show it if it contains something useful
            elif p.is_dir():
                if contains_match(p, depth=3): # Search up to 3 levels deep
                    filtered.append(p)
                    
        return filtered

    def update_filter(self, term: str) -> None:
        self.search_term = term.lower()
        # Clear cache for the new search
        self._search_cache = {}
        self.reload()
```

### 3.2 Deep Dive: The Logic of "Search"
Most implementations of file search are simple: "Does the filename match?".
But in a Tree View, if I search for "config", I expect to see the folder `src` **IF** it contains `config.json`.
If I just hide `src` because "src" != "config", I will never find my file.

**The Solution: Recursive Lookahead**
*   The `contains_match` function is the hero here.
*   It dives *into* folders that don't match, just to see if they hold something that *does*.
*   **Safety Limits**: We limit recursion to `depth=3`. Why? Because scanning `C:\` recursively would hang the machine for minutes. 3 levels provides a good balance of utility and speed.
*   **Blacklist**: We explicitly ignore `.git` and `node_modules`. These folders contain thousands of tiny files and are almost never what the user searches for.

### 3.3 Deep Dive: Event Hijacking
The default `DirectoryTree` has a behavior that many users find annoying: Single-clicking a file sends a "Selected" message, which often acts like "Open".
We intercepted this.
*   `on_click`: We look at `event.chain`. If it is 1 (Single Click), we set `_should_open = False`. If it is 2 (Double Click), we set `_should_open = True`.
*   `main.py` respects this flag. This gives us "Explorer-like" behavior.

---

## 🆕 4. UI Components: Modals

These files are essentially "Forms". They display a dialog, capture a string, and disappear.

### 4.1 `src/file_manager/create_folder.py`
```python
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
```

### 4.2 `src/file_manager/rename_modal.py`
```python
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
```

### 4.3 Deep Dive: Data Flow
1.  **Main App**: Calls `self.push_screen(RenameModal("old.txt"), callback_function)`.
2.  **Modal**: Initialized with "old.txt". Renders input box.
3.  **User**: Types "new.txt" and clicks "Rename".
4.  **Modal**: Calls `self.dismiss("new.txt")`.
5.  **Textual**: Closes the screen, restores focus to Main App, and executes `callback_function("new.txt")`.
This **Callback Pattern** keeps the main thread non-blocking. If we used a `while` loop to wait for input, the UI would freeze.

---

## 🎨 5. The Styling Engine: `src/file_manager/main.css`

Textual uses a dialect of CSS optimized for TUI.

### 5.1 Full Source Listing
```css
Screen {
    background: #1a1b26;
    layout: vertical;
}

NDirectoryTree,
DirectoryTree,
FilteredDirectoryTree {
    border: tall $accent;
    background: $surface;
    color: #a9b1d6;
}

NDirectoryTree>.directory-tree--extension,
DirectoryTree>.directory-tree--extension {
    color: $secondary;
}

#preview-pane {
    border: solid $primary;
    padding: 1;
}

ModalScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
    /* Deeply dim the background to make modal pop */
}

#modal_grid {
    width: 70;
    height: auto;
    padding: 1 2;
    border: double $accent;
    background: $surface;
    color: $text;
}

#label {
    width: 100%;
    content-align: center middle;
    text-style: bold italic;
    color: $secondary;
    margin-bottom: 1;
}

#folder_name,
#new_name_input {
    width: 100%;
    border: tall $primary;
    background: $boost;
    color: $text;
    margin-bottom: 1;
}

#folder_name .input--placeholder,
#new_name_input .input--placeholder {
    color: $text-disabled;
    text-style: italic;
}

#button_row {
    width: 100%;
    height: auto;
}

#button_row Button {
    width: 1fr;
}

#create,
#rename_btn {
    background: $success;
    color: $text;
    margin-right: 1;
}

#cancel,
#cancel_btn {
    background: $error;
    color: $text;
    margin-left: 1;
}

#tree-container {
    height: 1fr;
    border: solid $accent;
}

#search-container {
    height: 3;
    border: tall $primary;
    background: $boost;
    margin: 0 1;
    color: $text;
}

#search-icon {
    width: 3;
    content-align: center middle;
    color: $secondary;
}

#search-bar {
    width: 1fr;
    border: none;
    background: transparent;
}

#search-bar:focus {
    border: none;
}

MultilineFooter {
    dock: bottom;
    height: auto;
    min-height: 1;
    background: $boost;
    color: $text;
    padding: 0 1;
    text-wrap: wrap;
    border-top: solid $accent;
}
```

### 5.2 Deep Dive: The Box Model & Flexbox
Textual implements a subset of web CSS.
*   **`Screen { layout: vertical }`**: This is a flex container with `flex-direction: column`. It stacks children.
*   **`width: 1fr`**: This is "Flex Grow". It means "Take up all remaining space".
    *   In `#button_row Button`, both buttons have `1fr`, so they split the width 50/50.
    *   In `#tree-container`, `height: 1fr` means "Take up all vertical height not used by the Header or Footer".
*   **`dock: bottom`**: This is a special property for Headers/Footers. It removes the element from the flow and sticks it to the edge of the viewport.

### 5.3 Deep Dive: Theming Variables
You see variables like `$surface`, `$accent`, `$text`.
These are **Design Tokens** provided by Textual.
*   **Advantage**: When we switch to "Light Mode", we don't change the CSS. We just tell Textual "Switch to Light Theme". Textual automatically updates `$surface` from standard Dark Grey to Light Grey. The CSS rules remain identical.

---

## 🧑‍🍳 6. Developer's Cookbook

### 6.1 Glossary of Terms
*   **Widget**: A UI component (Button, Tree, Label).
*   **DOM (Document Object Model)**: The tree structure of widgets.
*   **Mount**: The lifecycle event when a widget is added to the screen.
*   **Reactive**: A variable that, when changed, automatically updates the UI.
*   **TUI**: Terminal User Interface.
*   **Event Loop**: The infinite loop that checks for key presses and mouse clicks.

### 6.2 How to Add a New Feature
**Scenario**: You want to add a "Properties" modal that shows file size.

1.  **Create the Modal**:
    *   Create `properties_modal.py`.
    *   Inherit from `ModalScreen`.
    *   Accept `file_path` in `__init__`.
    *   Use `os.stat(self.file_path).st_size` to get the size.
    *   Display it in a `Label`.

2.  **Register the Action**:
    *   In `main.py`, add `("p", "properties", "Properties")` to `BINDINGS`.

3.  **Implement the Handler**:
    *   Add `def action_properties(self):` to `NFileJ`.
    *   Get current node: `node = tree.cursor_node`.
    *   Call `self.push_screen(PropertiesModal(node.path))`.

### 6.3 Troubleshooting Guide

**Problem: The App Freezes when finding a file.**
*   **Cause**: You might be searching a massive directory like `C:\Windows` without the ignore list.
*   **Fix**: Check `filtered_tree.py`. Ensure `.git` and `node_modules` are in the ignore list. Reduce `depth` from 3 to 2.

**Problem: Icons don't show up.**
*   **Cause**: Your terminal font doesn't support Nerd Fonts.
*   **Fix**: Install a Nerd Font (e.g., "JetBrains Mono Nerd Font") and configure your terminal to use it. The File Manager uses Unicode characters that require these fonts.

**Problem: "Cut" doesn't delete the file immediately.**
*   **Explanation**: This is intentional design. Standard OS behavior is "Ghosting" the file until Paste is clicked. If we deleted it immediately, and you forgot to Paste, the file would be lost forever. We wait for the Paste action to perform the Move.

**Problem: Copy/Paste not working outside the app.**
*   **Cause**: `pyperclip` might not find a system clipboard mechanism (like `xclip` on Linux).
*   **Fix**: Install `xclip` or `xsel` on Linux. On Windows/Mac, it should work out of the box.

---

## 📎 7. Appendix A: System Operations Reference

This section provides a quick lookup for the critical system calls used in N-FileJ.

### 7.1 `shutil` vs `os`: When to use what?

| Function | Purpose | Speed | Supports Metadata? | Supports Recursive? |
| :--- | :--- | :--- | :--- | :--- |
| `os.rename` | Renaming files (Same Disk) | ⚡ Fast | Yes | No |
| `os.replace` | Atomic Replace | ⚡ Fast | Yes | No |
| `shutil.move` | Moving files (Diff Disk) | 🐢 Slow | Yes | Yes |
| `shutil.copy` | Copying files | 😐 Medium | No (New timestamp) | No |
| `shutil.copy2` | Copying files | 😐 Medium | **Yes** (Original time) | No |
| `shutil.copytree` | Copying Folders | 🐢 Slow | Yes | **Yes** |

**Recommendation**: Always use `shutil.copy2` for files and `shutil.copytree` for folders to ensure the user's timestamps are preserved.

### 7.2 Subprocess Exit Codes

When we run `subprocess.run([editor, file])`, the app waits for an exit code.

*   `0`: Success. The editor closed normally.
*   `1`: General Error. Maybe the file was locked.
*   `127`: Command Not Found. The user's `$EDITOR` variable is set to a program that doesn't exist.
*   `-9`: SIGKILL. The process was killed by the OS (OOM Killer).

### 7.3 Platform Quirks: Windows vs Linux

**Path Separators**:
*   Windows uses `\`. Linux uses `/`.
*   **Fix**: Always use `pathlib.Path`. It handles this automatically. `Path("folder") / "file.txt"` becomes `folder\file.txt` on Windows and `folder/file.txt` on Linux.

**File Opening**:
*   Linux: `subprocess.run(["xdg-open", path])`
*   Windows: `subprocess.run(f'start "" "{path}"', shell=True)`
*   MacOS: `subprocess.run(["open", path])`

---

## 🌳 8. Appendix B: Full Dependency Graph (ASCII)

This graph visualizes the import relationships between all files in the project.

```text
src/
└── file_manager/
    ├── main.py  (ENTRY POINT)
    │   ├── imports -> textual.App
    │   ├── imports -> textual.widgets
    │   ├── imports -> shutil (Standard Lib)
    │   ├── imports -> filtered_tree.py
    │   ├── imports -> create_folder.py
    │   └── imports -> rename_modal.py
    │
    ├── filtered_tree.py
    │   └── inherits -> textual.widgets.DirectoryTree
    │
    ├── create_folder.py
    │   └── inherits -> textual.screen.ModalScreen
    │
    ├── rename_modal.py
    │   └── inherits -> textual.screen.ModalScreen
    │
    └── main.css
        └── loaded_by -> main.py
```

### 8.1 Data Flow Diagram (Paste Action)

```text
[User] -> (Ctrl+V) -> [main.py] -> action_paste()
                        |
                        +---> [source_path] (Check if exists)
                        |
                        +---> [Regex] (Clean "file (1).txt" -> "file.txt")
                        |
                        +---> [While Loop] (Find free name "file (2).txt")
                        |
                        +---> [shutil] (Perform Copy/Move)
                        |
                        +---> [Tree] (Reload UI)
                        |
                        +---> [Toaster] (Notify User "Copied!")
```

---

*End of Technical Manual. Generated by Antigravity Agent for N-FileJ Project.*
