"""Scans a folder for Markdown files."""

from pathlib import Path
from typing import List

DEFAULT_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd"}


def scan_for_markdown(
    root: Path,
    recursive: bool = True,
    extensions: set = None,
) -> List[Path]:
    """Return a sorted list of Markdown file paths found under *root*.

    Parameters
    ----------
    root : Path
        Directory to scan.
    recursive : bool
        If True, scan subdirectories as well.
    extensions : set, optional
        File suffixes to match (default: .md, .markdown, .mdown, .mkd).
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    root = Path(root)
    if not root.is_dir():
        return []

    pattern = "**/*" if recursive else "*"
    found = [
        p for p in root.glob(pattern)
        if p.is_file() and p.suffix.lower() in extensions
    ]
    return sorted(found)
