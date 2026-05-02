"""
Friedrich - Document Reader - Obsidian Inspired UI
Features: Multi-tabs, NavRail, SidePanel, Empty State
"""

import argparse
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterweb import HtmlFrame
import urllib.parse
import webbrowser
from pathlib import Path

from constants import (
    APP_DIR, DARK_COLORS, LIGHT_COLORS, FONT, FONT_MONO,
    discover_themes,
)
from app_context import AppContext
from settings_manager import (
    load_settings, save_settings as _do_save_settings, ensure_on_screen,
)
from i18n import init_i18n
from widgets.diagram_viewer import DiagramViewer
from widgets.sidebar import SidePanel
from widgets.nav_rail import NavRail
from widgets.tab_manager import TabManager
from widgets.empty_state import EmptyState
from widgets.toolbar import Toolbar, ToolbarCommands
from services.file_renderer import FileRenderer
from services.pdf_exporter import export_pdf
from services.rd_parser import parse_rd


class MarkdownReader(tk.Tk):

    def __init__(self):
        super().__init__()
        from i18n import get_i18n
        
        self.title("Friedrich - Document Reader")

        themes = discover_themes()
        theme_names = list(themes.keys())

        self._ctx = AppContext(
            root=self,
            colors=dict(DARK_COLORS),
            scan_dir=APP_DIR,
            themes=themes,
            theme_names=theme_names,
            css_path=themes[theme_names[0]] if theme_names else None,
            i18n=get_i18n(),
        )
        ctx = self._ctx
        self._renderer = FileRenderer(ctx)
        
        ctx.save_settings = self._save_settings
        ctx.show_toast = self._show_toast
        ctx.load_file = self._load_file
        ctx.clear_viewer = self._clear_viewer

        self._show_home_screen = False

        self.colors = ctx.colors
        self.configure(bg=self.colors["bg"])

        icon_path = APP_DIR / "app_icon.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))

        geo = load_settings(ctx)
        self.colors = DARK_COLORS if ctx.ui_theme == "dark" else LIGHT_COLORS
        ctx.colors.clear()
        ctx.colors.update(self.colors)
        self.configure(bg=self.colors["bg"])
        self.geometry(geo)
        self.update_idletasks()
        self.after(50, lambda: ensure_on_screen(self))

        self._apply_styles()
        self._build_toolbar()
        self._build_main_layout()
        self._build_status_bar()
        self.status_frame.pack_forget()

        self._refresh_all()

        if ctx.current_file and ctx.current_file.exists():
            self.after(100, lambda: self._load_file(ctx.current_file))

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Global keyboard shortcuts (only bind once in __init__)
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Control-Shift-O>", lambda e: self._change_folder())
        self.bind_all("<Control-r>", lambda e: self._refresh_all())
        self.bind_all("<Control-b>", lambda e: self._toggle_sidebar())
        self.bind_all("<Control-f>", lambda e: self._focus_search())
        self.bind_all("<Escape>", self._on_escape)
        self.bind_all("<Alt-z>", lambda e: self._toggle_zen_mode())
        self.bind_all("<F11>", lambda e: self._toggle_zen_mode())
        self.bind_all("<Control-MouseWheel>", self._on_mouse_zoom)
        self.bind_all("<Control-KeyPress>", self._on_ctrl_keypress)

    def _save_settings(self):
        _do_save_settings(self._ctx)

    def _on_close(self):
        self._save_settings()
        self.destroy()

    def _focus_search(self):
        tab = self._ctx.current_tab
        if tab and tab.search_bar:
            tab.search_bar.focus()

    def _on_ctrl_keypress(self, event):
        if event.keysym in ("plus", "equal", "KP_Add"):
            self._zoom_in()
        elif event.keysym in ("minus", "underscore", "KP_Subtract"):
            self._zoom_out()
        elif event.keysym in ("0", "KP_0"):
            self._reset_zoom()

    def _on_mouse_zoom(self, event):
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _zoom_in(self):
        self._ctx.zoom_level = min(self._ctx.zoom_level + 10, 300)
        self._apply_zoom()

    def _zoom_out(self):
        self._ctx.zoom_level = max(self._ctx.zoom_level - 10, 50)
        self._apply_zoom()

    def _reset_zoom(self):
        self._ctx.zoom_level = 100
        self._apply_zoom()

    def _on_escape(self, event=None):
        if self._ctx.zen_mode:
            self._toggle_zen_mode()

    def _toggle_zen_mode(self):
        if not self._ctx.zen_mode:
            # Entering Zen Mode
            self._ctx.was_sidebar_visible = self._ctx.left_visible
            if self._ctx.left_visible:
                self._hide_sidebar_ui()
            
            self.titlebar.pack_forget()
            self.toolbar.pack_forget()
            self.toolbar_sep.pack_forget()
            self.status_frame.pack_forget()
            self._nav_rail.frame.pack_forget()
            self._tab_manager.hide_chrome()
            self._ctx.zen_mode = True
            self._show_toast(self._ctx.i18n.t("toast.zen_mode_on"), duration=3000, bg="#333333")
        else:
            # Exiting Zen Mode
            self.main_container.pack_forget()
            self.titlebar.pack(side=tk.TOP, fill=tk.X)
            self.toolbar.pack(side=tk.TOP, fill=tk.X)
            self.toolbar_sep.pack(side=tk.TOP, fill=tk.X)
            self.main_container.pack(fill=tk.BOTH, expand=True)
            self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
            self._nav_rail.frame.pack(side=tk.LEFT, fill=tk.Y, before=self.main_paned)
            self._tab_manager.show_chrome()
            
            if getattr(self._ctx, "was_sidebar_visible", True):
                self._show_sidebar_ui()
            
            self._update_ui_state()
            self._ctx.zen_mode = False

    def _toggle_sidebar(self):
        """Toggle sidebar visibility with proper state tracking."""
        if self._ctx.left_visible:
            self._hide_sidebar_ui()
        else:
            self._show_sidebar_ui()

    def _show_sidebar_ui(self):
        """Internal helper to show sidebar without toggle logic loops."""
        btn = self._nav_rail._action_icons.get("toggle_sidebar")
        
        current_panes = [str(p) for p in self.main_paned.panes()]
        
        if str(self.sidebar_panel) not in current_panes:
            self.main_paned.insert(0, self.sidebar_panel)
        
        # Restore saved width or use default
        saved_width = getattr(self._ctx, "sidebar_width", 220)
        if saved_width < 100: saved_width = 220
        
        # Set weights - sidebar with weight 0 maintains fixed width
        self.main_paned.pane(self.sidebar_panel, weight=0)
        self.main_paned.pane(self.workspace_container, weight=1)
        
        self._ctx.left_visible = True
        if btn: btn.config(fg=self.colors["accent"])

    def _hide_sidebar_ui(self):
        """Internal helper to hide sidebar without toggle logic loops."""
        btn = self._nav_rail._action_icons.get("toggle_sidebar")
        current_panes = [str(p) for p in self.main_paned.panes()]
        
        if str(self.sidebar_panel) in current_panes:
            self.update_idletasks()
            actual_width = self.sidebar_panel.winfo_width()
            if actual_width > 50: 
                self._ctx.sidebar_width = actual_width
            
            # Remove sidebar from paned window using forget
            self.main_paned.forget(self.sidebar_panel)
            
        self._ctx.left_visible = False
        if btn: btn.config(fg=self.colors["secondary"])

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=self.colors["sidebar"], foreground=self.colors["text"],
                        fieldbackground=self.colors["sidebar"], borderwidth=0, rowheight=24, font=(FONT, 10),
                        bordercolor=self.colors["sidebar"], lightcolor=self.colors["sidebar"],
                        darkcolor=self.colors["sidebar"], relief="flat")
        style.map("Treeview", background=[('selected', self.colors["list_active"])],
                  foreground=[('selected', self.colors["text_bright"])],
                  bordercolor=[('focus', self.colors["sidebar"]),
                               ('active', self.colors["sidebar"]),
                               ('!focus', self.colors["sidebar"])],
                  lightcolor=[('focus', self.colors["sidebar"])],
                  darkcolor=[('focus', self.colors["sidebar"])])
        style.configure("TPanedwindow", background=self.colors["sidebar"])
        style.configure("TFrame", background=self.colors["sidebar"])
        style.configure("TLabel", background=self.colors["sidebar"], foreground=self.colors["text"])
        style.configure("Sash", sashthickness=1, background=self.colors["sidebar"])

    def _build_toolbar(self):
        commands = ToolbarCommands(
            open_file=self.open_file, change_folder=self._change_folder, export_pdf=self._export_pdf,
            toggle_sidebar=self._toggle_sidebar, toggle_zen=self._toggle_zen_mode,
            toggle_view=self._toggle_view, go_back=self._go_back, toggle_ui_theme=self._toggle_ui_theme,
            refresh_all=self._refresh_all, copy_content=self._copy_content,
            clear_diagram_cache=self._clear_diagram_cache, zoom_in=self._zoom_in,
            zoom_out=self._zoom_out, reset_zoom=self._reset_zoom,
            toggle_status_bar=self._toggle_status_bar, set_markdown_theme=self._set_markdown_theme,
            quit=self.quit,
        )
        self._toolbar = Toolbar(self, self._ctx, commands)
        self.titlebar = self._toolbar.titlebar
        self.toolbar = self._toolbar.frame
        self.toolbar_sep = self._toolbar.separator

    def _build_status_bar(self):
        self.status_frame = tk.Frame(self, bg=self.colors["statusbar"], height=22)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_frame.pack_propagate(False)
        self.status_label = tk.Label(self.status_frame, text=self._ctx.i18n.t("status.ready"), bg=self.colors["statusbar"],
                                     fg=self.colors["statusbar_text"], font=(FONT, 9), anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

    def _build_main_layout(self):
        self.main_container = tk.Frame(self, bg=self.colors["bg"])
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 1. NavRail (ESTREMA SINISTRA)
        nav_commands = {
            "toggle_sidebar": self._toggle_sidebar,
            "toggle_view": self._toggle_view,
            "toggle_zen": self._toggle_zen_mode,
            "toggle_ui_theme": self._toggle_ui_theme,
            "help": lambda: self._toolbar.show_about(),
        }
        self._nav_rail = NavRail(self.main_container, self._ctx, commands=nav_commands)
        self._nav_rail.frame.pack(side=tk.LEFT, fill=tk.Y)
        if self._ctx.left_visible:
            self._nav_rail._action_icons["toggle_sidebar"].config(fg=self.colors["accent"])

        # 2. PanedWindow per Sidebar e Workspace
        self.main_paned = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL)
        self.main_paned.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 3. Sidebar
        self._sidebar = SidePanel(self.main_paned, self._ctx)
        self.sidebar_panel = self._sidebar.panel
        self._ctx.update_recent_list = self._sidebar.update_bookmarks_list
        self.main_paned.add(self.sidebar_panel, weight=0)

        # 4. Workspace Container
        self.workspace_container = tk.Frame(self.main_paned, bg=self.colors["bg"])
        self.main_paned.add(self.workspace_container, weight=1)
        
        self._tab_manager = TabManager(self.workspace_container, self._ctx, on_tab_change=self._on_tab_change)
        self._tab_manager.main_frame.pack(fill=tk.BOTH, expand=True)
        self._empty_state = EmptyState(self._tab_manager.content_area, self._ctx, on_open_file=self.open_file)

        self._update_ui_state()

    def _on_tab_change(self, tab):
        if tab:
            self._show_home_screen = False
            self._update_renderer_refs(tab)
            self.title(f"{tab.path.name} - Friedrich - Document Reader")
            if tab.path.exists():
                try:
                    current_mtime = tab.path.stat().st_mtime
                except OSError:
                    current_mtime = 0.0

                fragment = getattr(self, "_pending_fragment", None)
                self._pending_fragment = None

                is_pdf = tab.pdf_viewer is not None
                is_rd = tab.rsvp_player is not None
                if is_rd:
                    tab.rendered = True
                    tab.last_mtime = current_mtime
                elif tab.rendered and tab.last_mtime == current_mtime and (not fragment or is_pdf):
                    pass  # DOM still in tab.html_frame / pdf_viewer; skip re-render
                elif is_pdf:
                    self._renderer.load_file(tab.path, push_history=False)
                    tab.rendered = True
                    tab.last_mtime = current_mtime
                else:
                    self._renderer.load_file(tab.path, push_history=False, fragment=fragment)
                    tab.rendered = True
                    tab.last_mtime = current_mtime
        self._update_ui_state()

    def _update_renderer_refs(self, tab):
        self._ctx.html_frame = tab.html_frame
        self._ctx.source_text = tab.source_text

    def _update_ui_state(self):
        tab = self._ctx.current_tab
        has_tabs = len(self._ctx.open_tabs) > 0
        
        # Disable/Enable toggle_view based on content presence
        self._nav_rail.set_enabled("toggle_view", has_tabs)

        if self._show_home_screen or not has_tabs:
            if tab:
                tab.container.pack_forget()
            self._empty_state.frame.pack(fill=tk.BOTH, expand=True)
            if not self._ctx.open_tabs:
                self.title("Friedrich - Document Reader")
        else:
            self._empty_state.frame.pack_forget()
            if tab:
                tab.container.pack(fill=tk.BOTH, expand=True)

    def _show_home(self):
        self._show_home_screen = True
        self._update_ui_state()

    def _load_file(self, path: Path, push_history: bool = True, force_reload: bool = False, fragment: str | None = None):
        self._show_home_screen = False
        if push_history and self._ctx.current_file and self._ctx.current_file != path:
            self._ctx.history.append(self._ctx.current_file)
            self._ctx.forward_history.clear()

        self._pending_fragment = fragment
        for i, tab in enumerate(self._ctx.open_tabs):
            if tab.path == path:
                self._tab_manager.select_tab(i)
                return

        self._tab_manager.add_tab(path)

    def _refresh_all(self):
        self._ctx.tree_cache.clear()
        self._sidebar.build_tree(self._ctx.scan_dir)
        self._sidebar.update_bookmarks_list()
        if self._ctx.current_file and self._ctx.current_file.exists():
            tab = self._ctx.current_tab
            if tab and tab.rsvp_player is not None:
                try:
                    tab.rsvp_player.load(parse_rd(tab.path))
                except OSError:
                    pass
            else:
                self._renderer.load_file(self._ctx.current_file, push_history=False)
            if tab:
                try:
                    tab.last_mtime = tab.path.stat().st_mtime
                except OSError:
                    tab.last_mtime = 0.0
                tab.rendered = True

    def _clear_viewer(self):
        while self._ctx.open_tabs:
            self._tab_manager.close_tab(0)

    def _copy_content(self):
        tab = self._ctx.current_tab
        if not tab: return
        if tab.pdf_viewer is not None:
            return
        if tab.rsvp_player is not None:
            try:
                text = tab.path.read_text(encoding="utf-8")
            except Exception:
                return
            self.clipboard_clear()
            self.clipboard_append(text)
            self._show_toast(self._ctx.i18n.t("toast.copied"))
            return
        try:
            text = tab.source_text.get("1.0", tk.END).rstrip("\n") if tab.view_mode == "source" else tab.path.read_text(encoding="utf-8")
        except Exception: return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._show_toast(self._ctx.i18n.t("toast.copied"))

    def _show_toast(self, msg: str, duration: int = 2000, bg: str = None):
        if bg is None:
            bg = self.colors["accent"]
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=bg)
        tk.Label(toast, text=msg, bg=bg, fg="#ffffff", font=(FONT, 11, "bold"), padx=20, pady=10).pack()
        toast.update_idletasks()
        x = self.winfo_x() + self.winfo_width() - toast.winfo_width() - 20
        y = self.winfo_y() + 50
        toast.geometry(f"+{x}+{y}")
        toast.after(duration, toast.destroy)

    def _toggle_view(self):
        tab = self._ctx.current_tab
        if not tab: return
        if tab.pdf_viewer is not None:
            return
        if tab.rsvp_player is not None:
            return
        if tab.view_mode == "preview":
            tab.view_mode = "source"
            tab.html_frame.pack_forget()
            tab.source_text.pack(fill=tk.BOTH, expand=True, after=tab.search_bar.frame)
            ext = tab.path.suffix.lower()
            tab.source_text.delete("1.0", tk.END)
            try:
                content = f"File: {tab.path}\nSize: {tab.path.stat().st_size:,} bytes" if ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp") else tab.path.read_text(encoding="utf-8")
                tab.source_text.insert("1.0", content)
            except Exception:
                if not tab.path.exists():
                    tab.source_text.insert("1.0", "# " + tab.path.stem)
        else:
            tab.view_mode = "preview"
            tab.source_text.pack_forget()
            tab.html_frame.pack(fill=tk.BOTH, expand=True, after=tab.search_bar.frame)
            if tab.path.exists():
                self._renderer.load_file(tab.path, push_history=False)

    def open_file(self): self._renderer.open_file_dialog()

    def _on_link_click(self, url):
        tab = self._ctx.current_tab
        if not tab: return False
        if url.startswith("diagram:"):
            png_b64 = self._ctx.diagram_registry.get(url[8:])
            if png_b64: DiagramViewer(self, png_b64, self.colors)
            return False
        base_url, fragment = url.split("#", 1) if "#" in url else (url, None)
        base_url = urllib.parse.unquote(base_url)
        if fragment:
            fragment = urllib.parse.unquote(fragment)
        if base_url.startswith("file:"):
            path_str = base_url[8:] if base_url.startswith("file:///") else base_url[7:] if base_url.startswith("file://") else base_url[5:]
            if len(path_str) > 2 and path_str[1] == ":" and path_str[0] == "/": path_str = path_str[1:]
            path = Path(path_str)
        elif base_url.startswith(("http://", "https://", "mailto:")):
            if base_url.startswith(("http://", "https://")): webbrowser.open(url)
            return False
        elif not base_url or url.startswith("#"):
            if fragment and tab.path.exists():
                self._renderer.load_file(tab.path, push_history=False, fragment=fragment)
            return False
        else:
            path = Path(base_url)
            if not path.is_absolute(): path = (tab.path.parent / base_url).resolve()
        if not path.exists():
            for ext in ("", ".md", ".markdown", ".mdown", ".mkd"):
                matches = list(tab.path.parent.rglob(Path(base_url + ext).name)) or list(self._ctx.scan_dir.rglob(Path(base_url + ext).name))
                if matches: path = matches[0]; break
        if path.exists() and path.is_dir() and fragment and tab.path.exists():
            self._renderer.load_file(tab.path, push_history=False, fragment=fragment)
            return False
        if path.exists() and path.is_file(): self._load_file(path, fragment=fragment)
        return False

    def _go_back(self):
        if self._ctx.history:
            curr = self._ctx.current_file
            if curr: self._ctx.forward_history.append(curr)
            self._load_file(self._ctx.history.pop(), push_history=False)

    def _go_forward(self):
        if self._ctx.forward_history:
            curr = self._ctx.current_file
            if curr: self._ctx.history.append(curr)
            self._load_file(self._ctx.forward_history.pop(), push_history=False)

    def _toggle_status_bar(self):
        if self.status_frame.winfo_viewable(): self.status_frame.pack_forget()
        else: self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

    def _set_markdown_theme(self, name):
        self._ctx.theme_index = self._ctx.theme_names.index(name); self._ctx.css_path = self._ctx.themes[name]
        if self._ctx.view_mode == "preview" and self._ctx.current_file: self._renderer.load_file(self._ctx.current_file, push_history=False)
        self._save_settings()

    def _clear_diagram_cache(self):
        from services.diagram_cache import clear; clear(); self._show_toast(self._ctx.i18n.t("success.cache_cleared"), bg="#f39c12")
        self.after(500, self._refresh_all)

    def _toggle_ui_theme(self):
        self._ctx.ui_theme = "light" if self._ctx.ui_theme == "dark" else "dark"
        self.colors = LIGHT_COLORS if self._ctx.ui_theme == "light" else DARK_COLORS
        self._save_settings()
        current_file = self._ctx.current_file
        open_files = [tab.path for tab in self._ctx.open_tabs]
        self._ctx.open_tabs.clear()
        for widget in self.winfo_children(): widget.destroy()
        self._ctx.colors.clear(); self._ctx.colors.update(self.colors); self.configure(bg=self.colors["bg"])
        self._apply_styles(); self._build_toolbar(); self._build_main_layout(); self._build_status_bar(); self._refresh_all()
        for file_path in open_files:
            if file_path.exists():
                self._load_file(file_path, push_history=False)
        if current_file and current_file.exists():
            self._load_file(current_file, push_history=False)

    def _apply_zoom(self): self._renderer.apply_zoom()
    def _change_folder(self):
        folder = filedialog.askdirectory()
        if folder: self._ctx.scan_dir = Path(folder); self._refresh_all()
    def _export_pdf(self): export_pdf(self._ctx, self._renderer)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Friedrich - Document Reader - Modern Document Viewer",
        prog="md_reader"
    )
    parser.add_argument(
        "--lang", 
        choices=["en", "it"],
        default="en",
        help="Language for the application (en=English, it=Italian)"
    )
    args = parser.parse_args()

    if sys.platform == "win32":
        try:
            import ctypes
            # AUMID kept stable across the "Markdown Reader" -> "Document Reader"
            # rebrand: changing it would invalidate existing taskbar pins and
            # require re-tagging the .lnk via scripts/set_lnk_appid.ps1.
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Friedrich.MarkdownReader")
        except Exception:
            pass

    # Initialize i18n before creating the app
    init_i18n(args.lang)

    app = MarkdownReader()
    app.mainloop()
