"""
Domain model for a tree node in the log structure.
Groups routing messages with their child log lines.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .log_line import LogLine


@dataclass
class TreeNode:
    """A routing group (collapsible) or a standalone line."""
    header: LogLine
    children: list[LogLine] = field(default_factory=list)

    def is_group(self) -> bool:
        """Check if this node has children (is a collapsible group)."""
        return len(self.children) > 0

    def child_count(self) -> int:
        """Get the number of child lines."""
        return len(self.children)

    def all_lines(self) -> list[LogLine]:
        """Get all lines (header + children)."""
        return [self.header] + self.children
