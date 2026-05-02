from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    import tkinter as tk
    from tkinterweb import HtmlFrame
    from i18n import I18nManager
    from widgets.search_bar import SearchBar


@dataclass
class TabInfo:
    path: Path
    view_mode: str = "preview"  # "preview" or "source"
    zoom_level: int = 100
    last_html_body: str = ""
    scroll_pos: float = 0.0
    rendered: bool = False
    last_mtime: float = 0.0
    # Widgets specific to this tab (created and managed by TabManager)
    container: Optional[tk.Frame] = None
    html_frame: Optional[HtmlFrame] = None
    pdf_viewer: Optional[tk.Widget] = None
    rsvp_player: Optional[tk.Widget] = None
    source_text: Optional[tk.Text] = None
    search_bar: Optional[SearchBar] = None


@dataclass
class AppContext:
    root: tk.Tk
    colors: dict[str, str]

    # Application state
    scan_dir: Path = field(default_factory=lambda: Path("."))
    open_tabs: list[TabInfo] = field(default_factory=list)
    active_tab_index: int = -1
    
    recent_files: list[Path] = field(default_factory=list)
    history: list[Path] = field(default_factory=list)
    forward_history: list[Path] = field(default_factory=list)
    bookmarks: list[Path] = field(default_factory=list)
    
    # Global settings / state
    ui_theme: str = "dark"
    themes: dict[str, Path] = field(default_factory=dict)
    theme_names: list[str] = field(default_factory=list)
    theme_index: int = 0
    css_path: Optional[Path] = None
    diagram_registry: dict[str, str] = field(default_factory=dict)
    
    zen_mode: bool = False
    left_visible: bool = True
    tree_cache: list[Path] = field(default_factory=list)
    
    # i18n Manager
    i18n: Optional[I18nManager] = None

    # Callbacks (set by orchestrator)
    load_file: Optional[Callable[[Path], None]] = None
    refresh_all: Optional[Callable] = None
    save_settings: Optional[Callable] = None
    show_toast: Optional[Callable] = None
    update_recent_list: Optional[Callable] = None
    clear_viewer: Optional[Callable] = None

    @property
    def current_tab(self) -> Optional[TabInfo]:
        if 0 <= self.active_tab_index < len(self.open_tabs):
            return self.open_tabs[self.active_tab_index]
        return None

    @property
    def current_file(self) -> Optional[Path]:
        tab = self.current_tab
        return tab.path if tab else None

    @property
    def view_mode(self) -> str:
        tab = self.current_tab
        return tab.view_mode if tab else "preview"

    @view_mode.setter
    def view_mode(self, value: str):
        tab = self.current_tab
        if tab:
            tab.view_mode = value

    @property
    def zoom_level(self) -> int:
        tab = self.current_tab
        return tab.zoom_level if tab else 100

    @zoom_level.setter
    def zoom_level(self, value: int):
        tab = self.current_tab
        if tab:
            tab.zoom_level = value
