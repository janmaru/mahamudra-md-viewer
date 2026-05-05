from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import TYPE_CHECKING

from constants import FONT, ICONS

if TYPE_CHECKING:
    from app_context import AppContext

SUPPORTED_EXTS = (
    ".md", ".markdown", ".mdown", ".mkd", ".txt", ".csv", ".log", ".pdf",
    ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".rd",
)
_MD_EXTS = (".md", ".markdown", ".mdown", ".mkd")


class SidePanel:
    def __init__(self, parent: tk.Widget, ctx: AppContext):
        self._ctx = ctx
        self._parent = parent
        self._recent_row_widgets: list[tk.Frame] = []
        self._bookmark_row_widgets: list[tk.Frame] = []
        self._sort_reverse = False
        self._disabled_items: set[str] = set()
        colors = ctx.colors

        self.panel = tk.Frame(parent, bg=colors["sidebar"], width=220)
        self.panel.pack_propagate(False)

        # Header Title
        self._header_frame = tk.Frame(self.panel, bg=colors["sidebar"], padx=12, pady=10)
        self._header_frame.pack(fill=tk.X)
        self._title_label = tk.Label(self._header_frame, text=ctx.i18n.t("sidebar.explorer"), font=(FONT, 9, "bold"),
                                     bg=colors["sidebar"], fg=colors["secondary"], anchor=tk.W)
        self._title_label.pack(side=tk.LEFT)

        # Content Area
        self._content_frame = tk.Frame(self.panel, bg=colors["sidebar"])
        self._content_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Explorer View Widgets
        self._explorer_frame = tk.Frame(self._content_frame, bg=colors["sidebar"])
        
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", lambda *args: self._filter_tree())
        filter_entry = tk.Entry(
            self._explorer_frame, textvariable=self._filter_var,
            bg=colors["input_bg"], fg=colors["text"], borderwidth=0,
            insertbackground=colors["text"], font=(FONT, 10),
            relief=tk.FLAT)
        filter_entry.pack(fill=tk.X, padx=8, pady=4, ipady=3)

        tree_container = tk.Frame(self._explorer_frame, bg=colors["sidebar"])
        tree_container.pack(fill=tk.BOTH, expand=True)
        self._tree = ttk.Treeview(tree_container, show="tree", selectmode="browse")
        tree_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._tree.tag_configure("disabled", foreground=colors["secondary"])
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Recent Files section under explorer
        self._recent_label = tk.Label(self._explorer_frame, text=ctx.i18n.t("sidebar.recent_files"), 
                                      bg=colors["sidebar"], fg=colors["secondary"], 
                                      font=(FONT, 8, "bold"), anchor=tk.W)
        self._recent_label.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        self._recent_container = tk.Frame(self._explorer_frame, bg=colors["sidebar"])
        self._recent_container.pack(fill=tk.X, padx=8)

        # 2. Bookmarks View Widgets
        self._bookmarks_frame = tk.Frame(self._content_frame, bg=colors["sidebar"])
        self._bookmarks_container = tk.Frame(self._bookmarks_frame, bg=colors["sidebar"])
        self._bookmarks_container.pack(fill=tk.BOTH, expand=True)

        # 3. Search View Widgets (Placeholder)
        self._search_frame = tk.Frame(self._content_frame, bg=colors["sidebar"])
        tk.Label(self._search_frame, text=ctx.i18n.t("sidebar.global_search"), bg=colors["sidebar"], 
                 fg=colors["secondary"], font=(FONT, 10)).pack(pady=20)

        self.set_view("explorer")

    def set_view(self, view_name: str):
        # Hide all
        self._explorer_frame.pack_forget()
        self._bookmarks_frame.pack_forget()
        self._search_frame.pack_forget()

        i18n = self._ctx.i18n
        if view_name == "explorer":
            self._title_label.config(text=i18n.t("sidebar.explorer"))
            self._explorer_frame.pack(fill=tk.BOTH, expand=True)
            self.update_recent_files()
        elif view_name == "bookmarks":
            self._title_label.config(text=i18n.t("sidebar.bookmarks"))
            self._bookmarks_frame.pack(fill=tk.BOTH, expand=True)
            self.update_bookmarks_list()
        elif view_name == "search":
            self._title_label.config(text=i18n.t("sidebar.search"))
            self._search_frame.pack(fill=tk.BOTH, expand=True)
        elif view_name == "settings":
             self._ctx.show_toast(self._ctx.i18n.t("toast.coming_soon", feature=self._ctx.i18n.t("word.settings")))
        elif view_name == "help":
             self._ctx.show_toast(self._ctx.i18n.t("toast.coming_soon", feature=self._ctx.i18n.t("word.help")))

    def toggle_sort(self):
        self._sort_reverse = not self._sort_reverse
        self.build_tree(self._ctx.scan_dir)
        toast_key = "toast.sort_za" if self._sort_reverse else "toast.sort_az"
        self._ctx.show_toast(self._ctx.i18n.t(toast_key))

    def build_tree(self, root_path: Path, parent: str = "", populate_cache: bool = True) -> None:
        if not parent:
            self._tree.delete(*self._tree.get_children())
            self._disabled_items.clear()
            parent = self._tree.insert("", "end",
                                       text=f"  {ICONS['folder_open']} {root_path.name}",
                                       open=True, values=[str(root_path)])

        try:
            def _sort_key(p: Path) -> tuple[bool, float]:
                try:
                    mtime = p.stat().st_mtime
                except OSError:
                    mtime = 0.0
                return (not p.is_dir(), -mtime)

            entries = sorted(root_path.iterdir(), key=_sort_key, reverse=self._sort_reverse)
        except PermissionError:
            return

        rd_by_stem: dict[str, Path] = {
            p.stem.lower(): p
            for p in entries
            if p.is_file() and p.suffix.lower() == ".rd"
        }
        paired_rd_paths: set[Path] = set()

        for p in entries:
            # Skip hidden folders
            if any(part.startswith('.') for part in p.relative_to(self._ctx.scan_dir).parts):
                continue
            ext = p.suffix.lower()

            # Skip .rd that has a matching .md sibling — it's rendered as a child below.
            if p.is_file() and ext == ".rd":
                stem = p.stem.lower()
                md_sibling = next(
                    (q for q in entries
                     if q.is_file() and q.suffix.lower() in _MD_EXTS and q.stem.lower() == stem),
                    None,
                )
                if md_sibling is not None:
                    continue

            icon = ICONS.get(ext, "\u2022") if p.is_file() else ICONS["folder"]

            # Check if file is supported
            is_disabled = p.is_file() and ext not in SUPPORTED_EXTS
            tags = ("disabled",) if is_disabled else ()

            item_id = self._tree.insert(parent, "end", text=f"  {icon}  {p.name}", values=[str(p)], tags=tags)

            if is_disabled:
                self._disabled_items.add(item_id)

            if populate_cache:
                self._ctx.tree_cache.append(p)

            # Attach matching .rd as child of this .md
            if p.is_file() and ext in _MD_EXTS:
                rd_path = rd_by_stem.get(p.stem.lower())
                if rd_path is not None and rd_path not in paired_rd_paths:
                    rd_icon = ICONS.get(".rd", "\u25b6")
                    self._tree.insert(
                        item_id, "end",
                        text=f"  {rd_icon}  {rd_path.name}",
                        values=[str(rd_path)],
                    )
                    paired_rd_paths.add(rd_path)
                    if populate_cache:
                        self._ctx.tree_cache.append(rd_path)
                    self._tree.item(item_id, open=True)

    def _filter_tree(self) -> None:
        query = self._filter_var.get().lower()
        self._tree.delete(*self._tree.get_children())
        self._disabled_items.clear()

        if not query:
            self.build_tree(self._ctx.scan_dir, populate_cache=False)
            return

        root_node = self._tree.insert("", "end",
                                      text=f"  {ICONS['folder_open']} {self._ctx.scan_dir.name}",
                                      open=True, values=[str(self._ctx.scan_dir)])
        for p in self._ctx.tree_cache:
            if query in p.name.lower():
                icon = ICONS.get(p.suffix.lower(), "\u2022") if p.is_file() else ICONS["folder"]
                
                # Check if file is supported
                is_disabled = p.is_file() and p.suffix.lower() not in SUPPORTED_EXTS
                tags = ("disabled",) if is_disabled else ()
                
                item_id = self._tree.insert(root_node, "end", text=f"  {icon}  {p.name}", values=[str(p)], tags=tags)
                
                if is_disabled:
                    self._disabled_items.add(item_id)

    def update_bookmarks_list(self) -> None:
        colors = self._ctx.colors
        for w in self._bookmark_row_widgets:
            w.destroy()
        self._bookmark_row_widgets.clear()

        for i, p in enumerate(self._ctx.bookmarks):
            ext = p.suffix.lower()
            icon = ICONS.get(ext, "\u2022")

            row = tk.Frame(self._bookmarks_container, bg=colors["sidebar"])
            row.pack(fill=tk.X)

            lbl = tk.Label(row, text=f"  {icon}  {p.name}", font=(FONT, 10),
                           bg=colors["sidebar"], fg=colors["text"],
                           anchor=tk.W, cursor="hand2")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn = tk.Label(row, text="\u00d7", font=(FONT, 10),
                           bg=colors["sidebar"], fg=colors["secondary"],
                           cursor="hand2", padx=8)
            btn.pack(side=tk.RIGHT)

            idx = i
            lbl.bind("<Button-1>", lambda e, j=idx: self._ctx.load_file(self._ctx.bookmarks[j]))
            btn.bind("<Button-1>", lambda e, j=idx: self._remove_bookmark(j))

            for widget in (row, lbl):
                widget.bind("<Enter>", lambda e, r=row, l=lbl: (
                    r.configure(bg=colors["list_active"]),
                    l.configure(bg=colors["list_active"])))
                widget.bind("<Leave>", lambda e, r=row, l=lbl, b=btn: (
                    r.configure(bg=colors["sidebar"]),
                    l.configure(bg=colors["sidebar"])))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=colors["text_bright"]))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(fg=colors["secondary"]))

            self._bookmark_row_widgets.append(row)
    
    def update_recent_files(self) -> None:
        """Update recent files list under explorer."""
        colors = self._ctx.colors
        for w in self._recent_row_widgets:
            w.destroy()
        self._recent_row_widgets.clear()

        for i, p in enumerate(self._ctx.recent_files):
            ext = p.suffix.lower()
            icon = ICONS.get(ext, "\u2022")

            row = tk.Frame(self._recent_container, bg=colors["sidebar"])
            row.pack(fill=tk.X, pady=2)

            lbl = tk.Label(row, text=f"  {icon}  {p.name}", font=(FONT, 9),
                           bg=colors["sidebar"], fg=colors["text"],
                           anchor=tk.W, cursor="hand2")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn = tk.Label(row, text="\u00d7", font=(FONT, 9),
                           bg=colors["sidebar"], fg=colors["secondary"],
                           cursor="hand2", padx=4)
            btn.pack(side=tk.RIGHT)

            idx = i
            lbl.bind("<Button-1>", lambda e, j=idx: self._ctx.load_file(self._ctx.recent_files[j]) if j < len(self._ctx.recent_files) else None)
            btn.bind("<Button-1>", lambda e, j=idx: self._remove_recent(j))

            for widget in (row, lbl):
                widget.bind("<Enter>", lambda e, r=row, l=lbl: (
                    r.configure(bg=colors["list_active"]),
                    l.configure(bg=colors["list_active"])))
                widget.bind("<Leave>", lambda e, r=row, l=lbl, b=btn: (
                    r.configure(bg=colors["sidebar"]),
                    l.configure(bg=colors["sidebar"])))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=colors["text_bright"]))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(fg=colors["secondary"]))

            self._recent_row_widgets.append(row)
    
    def _remove_recent(self, index: int) -> None:
        """Remove recent file at index."""
        if 0 <= index < len(self._ctx.recent_files):
            self._ctx.recent_files.pop(index)
            self.update_recent_files()
            self._ctx.save_settings()

    def _remove_bookmark(self, index: int) -> None:
        if 0 <= index < len(self._ctx.bookmarks):
            self._ctx.bookmarks.pop(index)
            self.update_bookmarks_list()
            self._ctx.save_settings()

    def _on_tree_select(self, event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        item = selection[0]
        
        # Check if item is disabled
        if item in self._disabled_items:
            self._tree.selection_remove(item)
            return
        
        values = self._tree.item(item, "values")
        if not values:
            return
        path = Path(values[0])

        if path.is_dir():
            if not self._tree.get_children(item):
                self.build_tree(path, parent=item, populate_cache=False)
            self._tree.item(item, open=not self._tree.item(item, "open"))
        elif path.suffix.lower() in SUPPORTED_EXTS:
            self._ctx.load_file(path)
