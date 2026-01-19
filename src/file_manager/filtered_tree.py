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
