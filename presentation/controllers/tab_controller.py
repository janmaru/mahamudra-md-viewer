"""
Tab management controller.
Handles tab operations logic, separate from tkinter UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app_context import AppContext, TabInfo


class TabController:
    """Controller for tab operations."""

    def __init__(self, ctx: AppContext):
        self._ctx = ctx

    def add_tab(self, path: Path) -> int:
        """Add a new tab and return its index."""
        from app_context import TabInfo
        tab = TabInfo(path=path)
        self._ctx.open_tabs.append(tab)
        return len(self._ctx.open_tabs) - 1

    def select_tab(self, index: int) -> Optional[TabInfo]:
        """Select a tab by index.
        
        Returns the selected tab or None if invalid index.
        """
        if not (0 <= index < len(self._ctx.open_tabs)):
            return None
        
        self._ctx.active_tab_index = index
        return self._ctx.open_tabs[index]

    def close_tab(self, index: int) -> bool:
        """Close a tab.
        
        Returns True if closed successfully.
        """
        if not (0 <= index < len(self._ctx.open_tabs)):
            return False
        
        self._ctx.open_tabs.pop(index)
        
        if not self._ctx.open_tabs:
            self._ctx.active_tab_index = -1
        else:
            new_idx = min(index, len(self._ctx.open_tabs) - 1)
            self._ctx.active_tab_index = new_idx
        
        return True

    def close_all_tabs(self):
        """Close all open tabs."""
        self._ctx.open_tabs.clear()
        self._ctx.active_tab_index = -1

    def get_current_tab(self) -> Optional[TabInfo]:
        """Get current active tab."""
        if self._ctx.active_tab_index >= 0 and self._ctx.active_tab_index < len(self._ctx.open_tabs):
            return self._ctx.open_tabs[self._ctx.active_tab_index]
        return None

    def has_tabs(self) -> bool:
        """Check if any tabs are open."""
        return len(self._ctx.open_tabs) > 0

    def get_tab_count(self) -> int:
        """Get number of open tabs."""
        return len(self._ctx.open_tabs)

    def get_tab_by_path(self, path: Path) -> Optional[TabInfo]:
        """Find a tab by file path.
        
        Returns the tab or None if not found.
        """
        for tab in self._ctx.open_tabs:
            if tab.path == path:
                return tab
        return None

    def get_tab_index_by_path(self, path: Path) -> int:
        """Find tab index by file path.
        
        Returns the index or -1 if not found.
        """
        for i, tab in enumerate(self._ctx.open_tabs):
            if tab.path == path:
                return i
        return -1

    def cycle_tab_next(self) -> Optional[TabInfo]:
        """Move to next tab.
        
        Returns the new active tab or None.
        """
        if not self._ctx.open_tabs:
            return None
        
        new_idx = (self._ctx.active_tab_index + 1) % len(self._ctx.open_tabs)
        self._ctx.active_tab_index = new_idx
        return self._ctx.open_tabs[new_idx]

    def cycle_tab_prev(self) -> Optional[TabInfo]:
        """Move to previous tab.
        
        Returns the new active tab or None.
        """
        if not self._ctx.open_tabs:
            return None
        
        new_idx = (self._ctx.active_tab_index - 1) % len(self._ctx.open_tabs)
        self._ctx.active_tab_index = new_idx
        return self._ctx.open_tabs[new_idx]

    def get_breadcrumb_parts(self, path: Path, max_parts: int = 3) -> list[str]:
        """Get breadcrumb path parts.
        
        Returns last N parts of path (default 3).
        """
        parts = list(path.parts)
        return parts[-max_parts:] if len(parts) > max_parts else parts
