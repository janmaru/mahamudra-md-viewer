from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from PIL import Image, ImageTk

from constants import FONT

if TYPE_CHECKING:
    from app_context import AppContext

LOGO_PATH = Path(__file__).resolve().parent.parent / "scripts" / "preview_icon_256.png"
LOGO_SIZE = 96

class EmptyState:
    def __init__(self, parent: tk.Widget, ctx: AppContext, on_open_file: Callable,
                 on_new_file: Callable):
        self._ctx = ctx
        colors = ctx.colors
        i18n = ctx.i18n

        self.frame = tk.Frame(parent, bg=colors["bg"])

        container = tk.Frame(self.frame, bg=colors["bg"])
        container.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        # A missing logo asset must not take down the whole window: degrade
        # gracefully to a text-only empty state.
        self._logo_photo = None
        try:
            logo_img = Image.open(LOGO_PATH).resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
            self._logo_photo = ImageTk.PhotoImage(logo_img)
        except (FileNotFoundError, OSError):
            self._logo_photo = None
        if self._logo_photo is not None:
            tk.Label(container, image=self._logo_photo, bg=colors["bg"]).pack(pady=20)

        # Title
        tk.Label(container, text=i18n.t("app.title"), font=(FONT, 16, "bold"),
                 bg=colors["bg"], fg=colors["text_bright"]).pack()

        # Subtitle
        tk.Label(container, text=i18n.t("empty_state.subtitle"), font=(FONT, 10),
                 bg=colors["bg"], fg=colors["secondary"]).pack(pady=(5, 30))

        shortcuts = [
            ("shortcuts.new_file", "Ctrl + N", on_new_file),
            ("shortcuts.open_file", "Ctrl + O", on_open_file),
            ("shortcuts.change_folder", "Ctrl + Shift + O", lambda: self._ctx.root._change_folder()),
        ]

        for key, keys, cmd in shortcuts:
            row = tk.Frame(container, bg=colors["bg"], pady=4)
            row.pack(fill=tk.X)
            
            lbl = tk.Label(row, text=i18n.t(key), font=(FONT, 10), 
                           bg=colors["bg"], fg=colors["text"], anchor=tk.W)
            lbl.pack(side=tk.LEFT)
            
            k_lbl = tk.Label(row, text=keys, font=(FONT, 9), bg=colors["badge"], 
                             fg=colors["secondary"], padx=6, pady=1)
            k_lbl.pack(side=tk.RIGHT, padx=(20, 0))
            
            # Hover effects
            for w in (row, lbl, k_lbl):
                w.bind("<Enter>", lambda e, r=row: r.configure(cursor="hand2"))
                w.bind("<Button-1>", lambda e, c=cmd: c())
