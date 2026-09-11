from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
from typing import TYPE_CHECKING, Callable
from tkinterweb import HtmlFrame

from constants import FONT, FONT_MONO, MD_SYNTAX_DARK, MD_SYNTAX_LIGHT
from app_context import TabInfo
from services.md_highlighter import MarkdownHighlighter
from services.file_renderer import IMAGE_EXTS
from widgets.line_numbers import LineNumbers
from widgets.current_line import CurrentLineHighlight
from widgets.search_bar import SearchBar
from widgets.pdf_viewer import PdfViewer
from widgets.rsvp_player import RsvpPlayer
from services.rd_parser import parse_rd

if TYPE_CHECKING:
    from app_context import AppContext

VIEW_MODES = ("preview", "source", "split")


class TabManager:
    def __init__(self, parent: tk.Widget, ctx: AppContext, on_tab_change: Callable,
                 on_source_changed: Callable[[TabInfo], None] | None = None,
                 source_key_bindings: dict[str, Callable] | None = None):
        self._ctx = ctx
        self._parent = parent
        self._on_tab_change = on_tab_change
        # Fired after a typing-driven edit marks the tab dirty (live preview hook).
        self._on_source_changed = on_source_changed
        # Extra key bindings installed on every editor widget; handlers run
        # with "break" so they replace the default Text class binding.
        self._source_key_bindings = source_key_bindings or {}
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
        ext = path.suffix.lower()
        is_pdf = ext == ".pdf"
        is_rd = ext == ".rd"
        if is_pdf:
            tab.pdf_viewer = PdfViewer(tab.container, self._ctx)
        elif is_rd:
            tab.rsvp_player = RsvpPlayer(tab.container)
            try:
                tab.rsvp_player.load(parse_rd(path))
            except OSError:
                pass
        else:
            self._build_document_views(tab)
        if is_pdf or is_rd:
            # Placeholder editor so shared code paths (zoom, copy) stay uniform.
            self._build_source_view(tab, tab.container, editable=False)
        else:
            tab.search_bar = SearchBar(tab.container, self._ctx, tab)
            tab.search_bar.frame.pack(side=tk.TOP, fill=tk.X)
            if ext in IMAGE_EXTS:
                # The source view of an image is metadata: never editable, never saved.
                tab.read_only = True
                tab.source_text.configure(state="disabled")
            else:
                self._bind_dirty(tab)

        self._ctx.open_tabs.append(tab)
        self.select_tab(len(self._ctx.open_tabs) - 1)
        self.refresh_tabs()

    def add_untitled_tab(self, virtual_path: Path):
        tab = TabInfo(path=virtual_path)
        tab.is_untitled = True
        tab.view_mode = "source"
        tab.container = tk.Frame(self.content_area, bg=self._ctx.colors["bg"])
        self._build_document_views(tab)
        tab.search_bar = SearchBar(tab.container, self._ctx, tab)
        tab.search_bar.frame.pack(side=tk.TOP, fill=tk.X)
        self._bind_dirty(tab)
        tab.source_text.edit_modified(False)

        self._ctx.open_tabs.append(tab)
        self.select_tab(len(self._ctx.open_tabs) - 1)
        self.refresh_tabs()
        tab.source_text.focus_set()

    def _build_document_views(self, tab: TabInfo):
        """Create the preview (HtmlFrame) and the editor inside a horizontal
        PanedWindow; ``apply_view_mode`` decides which panes are visible."""
        tab.view_paned = ttk.PanedWindow(tab.container, orient=tk.HORIZONTAL)
        tab.html_frame = HtmlFrame(tab.view_paned, messages_enabled=False,
                                   javascript_enabled=True,
                                   on_link_click=self._ctx.root._on_link_click)
        self._build_source_view(tab, tab.view_paned, editable=True)

    def _build_source_view(self, tab: TabInfo, parent: tk.Widget, editable: bool):
        tab.source_frame = tk.Frame(parent, bg=self._ctx.colors["bg"])
        # The gutter is packed first so it keeps the left edge; the editor then
        # fills what is left.
        tab.source_text = tk.Text(
            tab.source_frame, bg=self._ctx.colors["bg"],
            fg=self._ctx.colors["text_bright"],
            insertbackground=self._ctx.colors["text"], borderwidth=0,
            padx=20, pady=20, font=(FONT_MONO, 11),
            selectbackground=self._ctx.colors["selection"],
            selectforeground=self._ctx.colors["text_bright"],
            undo=True, wrap="word")
        source_scroll = ttk.Scrollbar(tab.source_frame, orient=tk.VERTICAL, command=tab.source_text.yview)

        if editable:
            colors = self._ctx.colors
            tab.line_numbers = LineNumbers(tab.source_frame, tab.source_text, colors,
                                           FONT_MONO, 11)
            tab.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
            source_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            tab.source_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            palette = MD_SYNTAX_DARK if self._ctx.ui_theme == "dark" else MD_SYNTAX_LIGHT
            tab.highlighter = MarkdownHighlighter(tab.source_text, palette, FONT_MONO, 11)
            tab.current_line = CurrentLineHighlight(tab.source_text, colors["hover"])

            def _on_yscroll(*args, _bar=source_scroll, _hl=tab.highlighter, _ln=tab.line_numbers):
                _bar.set(*args)
                _hl.on_scroll()
                _ln.on_scroll()
            tab.source_text.configure(yscrollcommand=_on_yscroll)

            # Anything that can move the caret or change the text: the gutter
            # and the current-line tag both follow it.
            def _caret_moved(_event=None, _ln=tab.line_numbers, _cl=tab.current_line):
                _cl.refresh()
                _ln.schedule()
            for seq in ("<KeyRelease>", "<ButtonRelease-1>", "<<Modified>>",
                        "<<CaretMoved>>", "<Configure>", "<MouseWheel>"):
                tab.source_text.bind(seq, _caret_moved, add="+")
            tab.source_text.after_idle(_caret_moved)

            def _guard_hidden_keys(event, _tab=tab):
                """In preview the editor is unmapped but may still hold the
                keyboard focus (the HtmlFrame cannot take it: Tk crashes on
                Tab there). Swallow anything that would type into the
                invisible buffer, while leaving shortcuts with Control or Alt
                to the global bindings."""
                if _tab.view_mode != "preview":
                    return None
                if event.state & 0x0004 or event.state & 0x0008 or event.state & 0x20000:
                    return None  # Control / Alt: a shortcut, not text
                if event.char and event.char.isprintable():
                    return "break"
                return None
            tab.source_text.bind("<Key>", _guard_hidden_keys, add="+")

            for sequence, handler in self._source_key_bindings.items():
                # A handler returning False declined and lets Tk apply its own
                # binding (Enter outside a list inserts a plain newline);
                # anything else, None included, swallows the key.
                tab.source_text.bind(
                    sequence, lambda e, h=handler: "break" if h() is not False else None)
        else:
            source_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            tab.source_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tab.source_text.configure(yscrollcommand=source_scroll.set)

    def apply_view_mode(self, tab: TabInfo, center_sash: bool = False):
        """Arrange the tab's PanedWindow according to ``tab.view_mode``.

        preview -> [html_frame]; source -> [source_frame];
        split   -> [source_frame | html_frame]. ``center_sash`` places the
        sash at 50% and is meant for the transition *into* split; tab
        switches keep whatever position the user dragged it to.
        No-op for PDF / RSVP tabs, which have no ``view_paned``.
        """
        paned = tab.view_paned
        if paned is None:
            return
        wanted = {
            "preview": [tab.html_frame],
            "source": [tab.source_frame],
            "split": [tab.source_frame, tab.html_frame],
        }.get(tab.view_mode, [tab.html_frame])

        current = [str(p) for p in paned.panes()]
        for widget in (tab.source_frame, tab.html_frame):
            if widget not in wanted and str(widget) in current:
                paned.forget(widget)
        current = [str(p) for p in paned.panes()]
        for pos, widget in enumerate(wanted):
            if str(widget) not in current:
                # ttk rejects a numeric index equal to the pane count: use "end".
                where = pos if pos < len(current) else "end"
                paned.insert(where, widget, weight=1)
                current.insert(pos, str(widget))

        if paned.winfo_manager() != "pack":
            if tab.search_bar is not None:
                paned.pack(fill=tk.BOTH, expand=True, after=tab.search_bar.frame)
            else:
                paned.pack(fill=tk.BOTH, expand=True)

        if len(wanted) == 2 and center_sash:
            self._center_sash(paned)

    @staticmethod
    def _center_sash(paned: ttk.PanedWindow, attempts: int = 10) -> None:
        """Place the sash at 50% once the paned window has laid out its panes.

        ttk sizes freshly inserted panes from their requested widths, so the
        second pane can collapse to zero until the sash is set explicitly. A
        sashpos issued before the first layout pass is overwritten by it, so
        the position is verified and the call retried briefly if needed.
        """
        def _try(remaining: int) -> None:
            try:
                if not paned.winfo_exists():
                    return
                paned.update_idletasks()
                width = paned.winfo_width()
                if width > 1 and len(paned.panes()) == 2:
                    target = width // 2
                    paned.sashpos(0, target)
                    if abs(paned.sashpos(0) - target) <= 2:
                        return
            except tk.TclError:
                return
            if remaining > 0:
                paned.after(30, lambda: _try(remaining - 1))
        paned.after(1, lambda: _try(attempts))

    def _bind_dirty(self, tab: TabInfo):
        def _on_modified(event=None):
            txt = tab.source_text
            if txt is None:
                return
            if not txt.edit_modified():
                return
            was_dirty = tab.is_dirty
            tab.is_dirty = True
            txt.edit_modified(False)
            if not was_dirty:
                self.refresh_tabs()
            if self._on_source_changed is not None:
                self._on_source_changed(tab)
        tab.source_text.bind("<<Modified>>", _on_modified, add="+")

    def mark_clean(self, tab: TabInfo):
        if tab.source_text is None:
            return
        tab.source_text.edit_modified(False)
        tab.is_dirty = False
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
            active_tab.pdf_viewer.pack(fill=tk.BOTH, expand=True)
        elif active_tab.rsvp_player is not None:
            active_tab.rsvp_player.pack(fill=tk.BOTH, expand=True)
        else:
            self.apply_view_mode(active_tab)

        self.refresh_tabs()
        self.update_breadcrumbs(active_tab.path)
        self._on_tab_change(active_tab)

    def close_tab(self, index: int, confirm: bool = True):
        if not (0 <= index < len(self._ctx.open_tabs)):
            return
        tab = self._ctx.open_tabs[index]
        if confirm and tab.is_dirty:
            i18n = self._ctx.i18n
            answer = messagebox.askyesnocancel(
                i18n.t("dialog.unsaved_title"),
                i18n.t("dialog.unsaved_message", name=tab.path.name),
            )
            if answer is None:
                return
            if answer:
                self.select_tab(index)
                root = self._ctx.root
                saver = getattr(root, "_save_current", None)
                if saver is None or not saver():
                    return
        # Re-find the index by reference: save_as / refresh may have mutated
        # the list ordering (currently they don't, but stay defensive).
        try:
            index = self._ctx.open_tabs.index(tab)
        except ValueError:
            return
        self._ctx.open_tabs.pop(index)
        if tab.highlighter is not None:
            tab.highlighter.cancel()
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
            
            label_text = ("\u25CF " if tab.is_dirty else "") + tab.path.name
            lbl = tk.Label(inner, text=label_text, font=(FONT, 9),
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
