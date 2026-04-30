"""
Use case: Refresh file system state.
Coordinates scanning and caching.
"""

from __future__ import annotations

from pathlib import Path


class RefreshFileSystemUseCase:
    """Use case for refreshing file system state."""

    def execute(self, ctx) -> bool:
        """Refresh file system cache and sidebar.
        
        Args:
            ctx: Application context
            
        Returns:
            True if successful.
        """
        ctx.tree_cache.clear()
        return True

    def scan_directory(self, path: Path) -> dict:
        """Scan a directory for files.
        
        Args:
            path: Directory path to scan
            
        Returns:
            Dictionary of file metadata.
        """
        if not path.is_dir():
            return {}

        try:
            from services.file_scanner import FileScanner
            scanner = FileScanner()
            return scanner.scan(path)
        except Exception:
            return {}
