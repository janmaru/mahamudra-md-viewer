"""
Domain model for file information and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    file_type: str = ""  # "markdown", "log", "text", etc.
    size: int = 0
    encoding: str = "utf-8"
    metadata: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Get file name."""
        return self.path.name

    @property
    def exists(self) -> bool:
        """Check if file exists."""
        return self.path.exists()

    def is_markdown(self) -> bool:
        """Check if this is a markdown file."""
        return self.file_type == "markdown" or self.path.suffix.lower() == ".md"

    def is_log(self) -> bool:
        """Check if this is a log file."""
        return self.file_type == "log" or self.path.suffix.lower() == ".log"
