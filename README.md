# N-FileJ

A TUI-Based File manager written in Python using [Textual](https://github.com/Textualize/textual).

## Features
- **Directory Navigation**: Browse your files and folders in a terminal-based interface.
- **File Opening**: Open files directly in your system's default editor (Windows) or the one defined in your `$EDITOR` environment variable (Linux/macOS).
- **Dark Mode**: Support for both light and dark themes.
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
- `^ / \`: Toggle Dark mode
- `Enter`: Open a file or expand/collapse a directory
- `Arrow Keys`: Navigate the file tree
