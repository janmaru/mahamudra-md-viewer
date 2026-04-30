"""
Use case: Render a log file.
Coordinates domain services to parse and structure log content.
"""

from __future__ import annotations

from typing import Optional

from domain.models import TreeNode
from domain.services import LogParserService


class RenderLogFileUseCase:
    """Use case for rendering Serilog log files."""

    def __init__(self):
        self._parser = LogParserService()

    def execute(self, content: str) -> list[TreeNode]:
        """Parse and structure log content.
        
        Args:
            content: Raw log file content
            
        Returns:
            List of TreeNode objects representing the structured log.
        """
        lines = self._parser.parse_lines(content)
        tree = self._parser.build_tree(lines)
        return tree

    def parse_content(self, content: str) -> list:
        """Parse log content into LogLine objects."""
        return self._parser.parse_lines(content)
