from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from constants import FONT

if TYPE_CHECKING:
    from app_context import AppContext, TabInfo


class SearchBar:
    def __init__(self, parent: tk.Widget, ctx: AppContext, tab: TabInfo):
        if tab.source_text is None:
            raise ValueError("SearchBar requires tab.source_text to be created before initialization")
        self._ctx = ctx
        self._tab = tab
        self._search_matches: list = []
        self._search_current = -1
        self._search_count = 0
        self._search_query = ""

        colors = ctx.colors

        self.frame = tk.Frame(parent, bg=colors["toolbar"], height=32)
        self.frame.pack_propagate(False)

        search_icon = tk.Label(self.frame, text="\U0001f50d", bg=colors["toolbar"],
                               fg=colors["secondary"], font=(FONT, 9))
        search_icon.pack(side=tk.LEFT, padx=(8, 2))

        self._entry = tk.Entry(
            self.frame, bg=colors["input_bg"], fg=colors["text_bright"],
            insertbackground=colors["text"], font=(FONT, 10), borderwidth=0,
            selectbackground=colors["selection"], selectforeground=colors["text_bright"])
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4), pady=4)
        self._entry.bind("<Return>", lambda e: self._on_enter())
        self._entry.bind("<Shift-Return>", lambda e: self.search_prev())
        self._entry.bind("<KeyRelease>", lambda e: self._on_keyrelease())

        self._clear_btn = tk.Label(self.frame, text="\u2715", bg=colors["toolbar"],
                                   fg=colors["secondary"], font=(FONT, 10), cursor="hand2")
        self._clear_btn.bind("<Button-1>", lambda e: self.clear())

        self._count_label = tk.Label(
            self.frame, text="", bg=colors["toolbar"],
            fg=colors["secondary"], font=(FONT, 9), width=8)
        self._count_label.pack(side=tk.LEFT, padx=4)

        prev_btn = tk.Label(self.frame, text="\u25b2", bg=colors["toolbar"],
                            fg=colors["secondary"], font=(FONT, 10), cursor="hand2")
        prev_btn.pack(side=tk.LEFT, padx=2)
        prev_btn.bind("<Button-1>", lambda e: self.search_prev())

        next_btn = tk.Label(self.frame, text="\u25bc", bg=colors["toolbar"],
                            fg=colors["secondary"], font=(FONT, 10), cursor="hand2")
        next_btn.pack(side=tk.LEFT, padx=2)
        next_btn.bind("<Button-1>", lambda e: self.search_next())

        tab.source_text.tag_configure("search_match", background="#515c6a")
        tab.source_text.tag_configure("search_current", background="#613214")
        
        self._toggle_clear_button()

    def focus(self) -> None:
        self._entry.focus_set()
        self._entry.select_range(0, tk.END)

    def clear(self) -> None:
        self._entry.delete(0, tk.END)
        self._clear_highlights()
        self._count_label.config(text="")
        self._toggle_clear_button()

    def _toggle_clear_button(self):
        if self._entry.get():
            if not self._clear_btn.winfo_viewable():
                self._clear_btn.pack(side=tk.LEFT, padx=2, before=self._count_label)
        else:
            self._clear_btn.pack_forget()

    def _on_keyrelease(self):
        self._toggle_clear_button()
        query = self._entry.get()
        if not query:
            self._clear_highlights()
            self._count_label.config(text="")
            return
        self._do_search(query)

    def _on_enter(self):
        query = self._entry.get()
        if not query:
            return
        if self._search_query == query and self._search_count > 0:
            self.search_next()
        else:
            self._do_search(query)

    def _do_search(self, query: str):
        self._search_query = query
        if self._tab.view_mode == "source":
            self._search_in_source(query)
        else:
            self._search_in_preview(query)

    def _search_in_source(self, query: str):
        source = self._tab.source_text
        source.tag_remove("search_match", "1.0", tk.END)
        source.tag_remove("search_current", "1.0", tk.END)
        self._search_matches.clear()
        self._search_current = -1

        start = "1.0"
        while True:
            pos = source.search(query, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self._search_matches.append((pos, end))
            source.tag_add("search_match", pos, end)
            start = end

        self._search_count = len(self._search_matches)
        if self._search_count > 0:
            self._search_current = 0
            self._highlight_current_source_match()
            self._count_label.config(text=f"1/{self._search_count}")
        else:
            self._count_label.config(text=self._ctx.i18n.t("search.no_results"))

    def _search_in_preview(self, query: str):
        self._search_current = 0
        count = self._tab.html_frame.find_text(query, select=1, ignore_case=True, highlight_all=True)
        self._search_count = count
        if count > 0:
            self._count_label.config(text=f"1/{count}")
        else:
            self._count_label.config(text=self._ctx.i18n.t("search.no_results"))

    def _highlight_current_source_match(self):
        source = self._tab.source_text
        source.tag_remove("search_current", "1.0", tk.END)
        if 0 <= self._search_current < len(self._search_matches):
            pos, end = self._search_matches[self._search_current]
            source.tag_add("search_current", pos, end)
            source.see(pos)

    def search_next(self):
        if self._search_count <= 0:
            return
        if self._tab.view_mode == "source":
            self._search_current = (self._search_current + 1) % self._search_count
            self._highlight_current_source_match()
        else:
            self._search_current = (self._search_current + 1) % self._search_count
            self._tab.html_frame.find_text(self._search_query, select=self._search_current + 1,
                                           ignore_case=True, highlight_all=True)
        self._count_label.config(
            text=f"{self._search_current + 1}/{self._search_count}")

    def search_prev(self):
        if self._search_count <= 0:
            return
        if self._tab.view_mode == "source":
            self._search_current = (self._search_current - 1) % self._search_count
            self._highlight_current_source_match()
        else:
            self._search_current = (self._search_current - 1) % self._search_count
            self._tab.html_frame.find_text(self._search_query, select=self._search_current + 1,
                                           ignore_case=True, highlight_all=True)
        self._count_label.config(
            text=f"{self._search_current + 1}/{self._search_count}")

    def _clear_highlights(self):
        if self._tab.view_mode == "source":
            source = self._tab.source_text
            source.tag_remove("search_match", "1.0", tk.END)
            source.tag_remove("search_current", "1.0", tk.END)
        else:
            self._tab.html_frame.find_text("", highlight_all=True)
        self._search_matches.clear()
        self._search_current = -1
        self._search_count = 0
        self._search_query = ""
