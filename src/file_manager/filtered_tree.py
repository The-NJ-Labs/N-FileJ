from pathlib import Path
from textual.widgets import DirectoryTree

class FilteredDirectoryTree(DirectoryTree):
    search_term: str = ""

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        # This is the magic method. It decides what files to SHOW.
        if not self.search_term:
            return paths
        
        return [
            path for path in paths 
            if self.search_term.lower() in path.name.lower()
        ]

    def update_filter(self, term: str) -> None:
        self.search_term = term
        self.reload() # This forces the tree to call filter_paths again 
