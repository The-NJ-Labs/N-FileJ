# N-FileJ

A TUI-Based File manager written in Python using [Textual](https://github.com/Textualize/textual).

## Features
- **Directory Navigation**: Browse your files and folders in a terminal-based interface.
- **File Opening**: Open files directly in your system's default editor (Windows) or the one defined in your `$EDITOR` environment variable (Linux/macOS).
- **Dark Mode**: Support for both light and dark themes.
- **Many Themes**: Includes all Textual themes
- **Lightweight**: fast and simple, built for the terminal.

## Installation

Install using `pipx` (recommended):
```bash
pipx install n-filej
```

Or via `uv`:
```bash
uv tool install n-filej
```

Or via `pip`:
```bash
pip install n-filej
```

## Usage
Simply run:
```bash
n-filej
```

## Keybindings
- `Q`: Quit the application
- `Alt+T`: Toggle Dark mode
- `Alt+Shift+N`: Create a new folder
- `Delete`: Delete a folder/file
- `F2`: Rename a folder/file
- `Enter`: Open a file or expand/collapse a directory
- `Arrow Keys`: Navigate the file tree
