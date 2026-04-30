"""
Main application controller.
Handles application logic and command execution, separate from tkinter UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from domain.models import FileInfo

if TYPE_CHECKING:
    from app_context import AppContext


class MainController:
    """Controller for main application logic."""

    def __init__(self, ctx: AppContext):
        self._ctx = ctx
        self._show_home_screen = False

    @property
    def show_home_screen(self) -> bool:
        """Check if home screen should be shown."""
        return self._show_home_screen

    @show_home_screen.setter
    def show_home_screen(self, value: bool):
        self._show_home_screen = value

    def load_file(self, path: Path, push_history: bool = True, force_reload: bool = False) -> bool:
        """Load a file.
        
        Returns True if file was newly loaded/switched.
        """
        self._show_home_screen = False
        
        if push_history and self._ctx.current_file and self._ctx.current_file != path:
            self._ctx.history.append(self._ctx.current_file)
            self._ctx.forward_history.clear()

        for tab in self._ctx.open_tabs:
            if tab.path == path:
                return False  # Already open

        return True  # New file

    def show_home(self):
        """Show home/empty state screen."""
        self._show_home_screen = True

    def toggle_view(self, tab) -> str:
        """Toggle between preview and source view.
        
        Returns new view mode ("preview" or "source").
        """
        if not tab:
            return tab.view_mode if tab else "preview"

        if tab.view_mode == "preview":
            tab.view_mode = "source"
            ext = tab.path.suffix.lower()
            if ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"):
                return "image_metadata"  # Special case for images
        else:
            tab.view_mode = "preview"

        return tab.view_mode

    def toggle_zen_mode(self) -> bool:
        """Toggle zen mode.
        
        Returns new zen_mode state.
        """
        self._ctx.zen_mode = not self._ctx.zen_mode
        return self._ctx.zen_mode

    def toggle_sidebar(self) -> bool:
        """Toggle sidebar visibility.
        
        Returns new sidebar visibility state.
        """
        self._ctx.left_visible = not self._ctx.left_visible
        return self._ctx.left_visible

    def toggle_ui_theme(self) -> str:
        """Toggle UI theme (dark/light).
        
        Returns new theme name.
        """
        self._ctx.ui_theme = "light" if self._ctx.ui_theme == "dark" else "dark"
        return self._ctx.ui_theme

    def set_markdown_theme(self, theme_name: str):
        """Set markdown rendering theme."""
        if theme_name in self._ctx.themes:
            self._ctx.theme_index = self._ctx.theme_names.index(theme_name)
            self._ctx.css_path = self._ctx.themes[theme_name]

    def zoom_in(self):
        """Increase zoom level."""
        self._ctx.zoom_level = min(self._ctx.zoom_level + 10, 300)

    def zoom_out(self):
        """Decrease zoom level."""
        self._ctx.zoom_level = max(self._ctx.zoom_level - 10, 50)

    def reset_zoom(self):
        """Reset zoom level to 100%."""
        self._ctx.zoom_level = 100

    def go_back(self) -> Optional[Path]:
        """Navigate back in history.
        
        Returns the file to load or None.
        """
        if self._ctx.history:
            curr = self._ctx.current_file
            if curr:
                self._ctx.forward_history.append(curr)
            return self._ctx.history.pop()
        return None

    def go_forward(self) -> Optional[Path]:
        """Navigate forward in history.
        
        Returns the file to load or None.
        """
        if self._ctx.forward_history:
            curr = self._ctx.current_file
            if curr:
                self._ctx.history.append(curr)
            return self._ctx.forward_history.pop()
        return None

    def change_folder(self, folder_path: Path):
        """Change scan directory."""
        if folder_path.is_dir():
            self._ctx.scan_dir = folder_path
            self._ctx.tree_cache.clear()

    def refresh_all(self):
        """Refresh all UI and caches."""
        self._ctx.tree_cache.clear()

    def can_go_back(self) -> bool:
        """Check if can navigate back."""
        return len(self._ctx.history) > 0

    def can_go_forward(self) -> bool:
        """Check if can navigate forward."""
        return len(self._ctx.forward_history) > 0
