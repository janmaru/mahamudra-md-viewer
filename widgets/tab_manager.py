from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import TYPE_CHECKING, Callable
from tkinterweb import HtmlFrame

from constants import FONT, FONT_MONO
from app_context import TabInfo
from widgets.search_bar import SearchBar
from widgets.pdf_viewer import PdfViewer

if TYPE_CHECKING:
    from app_context import AppContext

class TabManager:
    def __init__(self, parent: tk.Widget, ctx: AppContext, on_tab_change: Callable):
        self._ctx = ctx
        self._parent = parent
        self._on_tab_change = on_tab_change
        colors = ctx.colors

        # Main Container (Workspace attivo)
        self.main_frame = tk.Frame(parent, bg=colors["bg"])
        
        # Header Container (Tabs)
        self.header_frame = tk.Frame(self.main_frame, bg=colors["toolbar"], height=34)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        self.header_frame.pack_propagate(False)

        self.scroll_left_btn = tk.Label(self.header_frame, text="\u2039", font=(FONT, 14, "bold"),
                                        bg=colors["toolbar"], fg=colors["secondary"],
                                        padx=8, cursor="hand2")
        self.scroll_left_btn.bind("<Button-1>", lambda e: self._scroll_tabs(-80))
        self.scroll_right_btn = tk.Label(self.header_frame, text="\u203a", font=(FONT, 14, "bold"),
                                         bg=colors["toolbar"], fg=colors["secondary"],
                                         padx=8, cursor="hand2")
        self.scroll_right_btn.bind("<Button-1>", lambda e: self._scroll_tabs(80))

        self.tabs_canvas = tk.Canvas(self.header_frame, bg=colors["toolbar"], height=34,
                                     highlightthickness=0, xscrollincrement=1)
        self.tabs_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tabs_container = tk.Frame(self.tabs_canvas, bg=colors["toolbar"])
        self._tabs_window_id = self.tabs_canvas.create_window(
            0, 0, anchor="nw", window=self.tabs_container, height=34)

        self.new_tab_btn = tk.Label(self.tabs_container, text="+", font=(FONT, 12, "bold"),
                                    bg=colors["toolbar"], fg=colors["secondary"],
                                    padx=10, cursor="hand2")
        self.new_tab_btn.bind("<Button-1>", lambda e: self._ctx.root._show_home())

        self.tabs_canvas.bind("<Configure>", lambda e: self._update_scroll_state())

        # Sub-Header (Navigation & Breadcrumbs)
        self.sub_header = tk.Frame(self.main_frame, bg=colors["bg"], height=38)
        self.sub_header.pack(side=tk.TOP, fill=tk.X)
        self.sub_header.pack_propagate(False)
        self.sub_header_sep = tk.Frame(self.main_frame, bg=colors["border"], height=1)
        self.sub_header_sep.pack(side=tk.TOP, fill=tk.X)

        self.breadcrumb_frame = tk.Frame(self.sub_header, bg=colors["bg"])
        self.breadcrumb_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Content Area
        self.content_area = tk.Frame(self.main_frame, bg=colors["bg"])
        self.content_area.pack(fill=tk.BOTH, expand=True)

        self._tab_buttons: list[tk.Frame] = []

    def add_tab(self, path: Path):
        tab = TabInfo(path=path)
        tab.container = tk.Frame(self.content_area, bg=self._ctx.colors["bg"])
        is_pdf = path.suffix.lower() == ".pdf"
        if is_pdf:
            tab.pdf_viewer = PdfViewer(tab.container, self._ctx)
        else:
            tab.html_frame = HtmlFrame(tab.container, messages_enabled=False,
                                       javascript_enabled=True,
                                       on_link_click=self._ctx.root._on_link_click)
        tab.source_text = tk.Text(
            tab.container, bg=self._ctx.colors["bg"],
            fg=self._ctx.colors["text_bright"],
            insertbackground=self._ctx.colors["text"], borderwidth=0,
            padx=20, pady=20, font=(FONT_MONO, 11),
            selectbackground=self._ctx.colors["selection"],
            selectforeground=self._ctx.colors["text_bright"])
        # Bind Ctrl+C to copy content from source view
        tab.source_text.bind("<Control-c>", lambda e: self._ctx.root._copy_content())
        if not is_pdf:
            tab.search_bar = SearchBar(tab.container, self._ctx, tab)
            tab.search_bar.frame.pack(side=tk.TOP, fill=tk.X)

        self._ctx.open_tabs.append(tab)
        self.select_tab(len(self._ctx.open_tabs) - 1)
        self.refresh_tabs()

    def select_tab(self, index: int):
        if not (0 <= index < len(self._ctx.open_tabs)):
            return

        if self._ctx.current_tab:
            self._ctx.current_tab.container.pack_forget()

        self._ctx.active_tab_index = index
        active_tab = self._ctx.open_tabs[index]

        active_tab.container.pack(fill=tk.BOTH, expand=True)
        if active_tab.pdf_viewer is not None:
            active_tab.source_text.pack_forget()
            active_tab.pdf_viewer.pack(fill=tk.BOTH, expand=True)
        elif active_tab.view_mode == "preview":
            active_tab.source_text.pack_forget()
            active_tab.html_frame.pack(fill=tk.BOTH, expand=True, after=active_tab.search_bar.frame)
        else:
            active_tab.html_frame.pack_forget()
            active_tab.source_text.pack(fill=tk.BOTH, expand=True, after=active_tab.search_bar.frame)

        self.refresh_tabs()
        self.update_breadcrumbs(active_tab.path)
        self._on_tab_change(active_tab)

    def close_tab(self, index: int):
        if not (0 <= index < len(self._ctx.open_tabs)):
            return
        tab = self._ctx.open_tabs.pop(index)
        tab.container.destroy()

        if not self._ctx.open_tabs:
            self._ctx.active_tab_index = -1
            self.refresh_tabs()
            self.update_breadcrumbs(None)
            self._on_tab_change(None)
        else:
            new_idx = min(index, len(self._ctx.open_tabs) - 1)
            self.select_tab(new_idx)

    def refresh_tabs(self):
        for btn in self._tab_buttons:
            btn.destroy()
        self._tab_buttons.clear()
        self.new_tab_btn.pack_forget()

        colors = self._ctx.colors
        for i, tab in enumerate(self._ctx.open_tabs):
            is_active = (i == self._ctx.active_tab_index)
            
            tab_btn = tk.Frame(self.tabs_container, bg=colors["toolbar"], padx=1)
            tab_btn.pack(side=tk.LEFT, fill=tk.Y)
            
            inner = tk.Frame(tab_btn, bg=colors["bg"] if is_active else colors["toolbar"], 
                             padx=12, pady=0)
            inner.pack(fill=tk.BOTH, expand=True)
            
            if is_active:
                indicator = tk.Frame(inner, bg=colors["accent"], height=2)
                indicator.pack(side=tk.TOP, fill=tk.X)
            
            lbl = tk.Label(inner, text=tab.path.name, font=(FONT, 9),
                           bg=colors["bg"] if is_active else colors["toolbar"],
                           fg=colors["text_bright"] if is_active else colors["text"])
            lbl.pack(side=tk.LEFT, pady=(4 if is_active else 6, 6))
            
            close_btn = tk.Label(inner, text="\u00d7", font=(FONT, 10),
                                 bg=colors["bg"] if is_active else colors["toolbar"],
                                 fg=colors["secondary"], cursor="hand2", padx=4)
            close_btn.pack(side=tk.LEFT, padx=(6, 0))
            
            idx = i
            lbl.bind("<Button-1>", lambda e, j=idx: self.select_tab(j))
            inner.bind("<Button-1>", lambda e, j=idx: self.select_tab(j))
            close_btn.bind("<Button-1>", lambda e, j=idx: self.close_tab(j))
            
            self._tab_buttons.append(tab_btn)
            if not is_active:
                tk.Frame(tab_btn, bg=colors["border"], width=1).pack(side=tk.RIGHT, fill=tk.Y, pady=8)

        self.new_tab_btn.pack(side=tk.LEFT, fill=tk.Y)
        self._update_scroll_state()

    def _scroll_tabs(self, dx: int):
        self.tabs_canvas.xview_scroll(dx, "units")

    def _update_scroll_state(self):
        self.tabs_container.update_idletasks()
        required = self.tabs_container.winfo_reqwidth()
        available = self.tabs_canvas.winfo_width()
        if available <= 1:
            self.tabs_canvas.after(50, self._update_scroll_state)
            return

        self.tabs_canvas.configure(scrollregion=(0, 0, required, 34))

        if required > available:
            self.scroll_left_btn.pack(side=tk.LEFT, fill=tk.Y, before=self.tabs_canvas)
            self.scroll_right_btn.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.scroll_left_btn.pack_forget()
            self.scroll_right_btn.pack_forget()
            self.tabs_canvas.xview_moveto(0)

    def hide_chrome(self):
        self.header_frame.pack_forget()
        self.sub_header.pack_forget()
        self.sub_header_sep.pack_forget()

    def show_chrome(self):
        self.header_frame.pack(side=tk.TOP, fill=tk.X, before=self.content_area)
        self.sub_header.pack(side=tk.TOP, fill=tk.X, before=self.content_area)
        self.sub_header_sep.pack(side=tk.TOP, fill=tk.X, before=self.content_area)

    def update_breadcrumbs(self, path: Path | None):
        for w in self.breadcrumb_frame.winfo_children():
            w.destroy()
        if not path: return
        
        colors = self._ctx.colors
        parts = list(path.parts)[-3:]
        for i, part in enumerate(parts):
            lbl = tk.Label(self.breadcrumb_frame, text=part, font=(FONT, 9),
                           bg=colors["bg"], fg=colors["text"] if i < len(parts)-1 else colors["text_bright"])
            lbl.pack(side=tk.LEFT)
            if i < len(parts) - 1:
                tk.Label(self.breadcrumb_frame, text=" / ", font=(FONT, 8),
                         bg=colors["bg"], fg=colors["secondary"]).pack(side=tk.LEFT)
