from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Callable

from constants import FONT
from widgets.tooltip import Tooltip

if TYPE_CHECKING:
    from app_context import AppContext


class NavRail:
    def __init__(self, parent: tk.Widget, ctx: AppContext, commands: dict[str, Callable]):
        self._ctx = ctx
        self._commands = commands
        colors = ctx.colors
        i18n = ctx.i18n

        self.frame = tk.Frame(parent, bg=colors["sidebar"], width=48)
        self.frame.pack(side=tk.LEFT, fill=tk.Y)
        self.frame.pack_propagate(False)

        self._action_icons: dict[str, tk.Label] = {}

        # Top: tutte le icone con spaziatura uniforme
        self._top_container = tk.Frame(self.frame, bg=colors["sidebar"])
        self._top_container.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))
        self._make_action_icon("toggle_sidebar", "\u2261", i18n.t("tooltip.toggle_sidebar"), self._top_container)
        self._make_action_icon("toggle_view", "\u25c9", i18n.t("tooltip.toggle_view"), self._top_container)
        self._make_action_icon("toggle_zen", "\u2726", i18n.t("tooltip.toggle_zen"), self._top_container)
        ui_icon = "\u25d0" if ctx.ui_theme == "dark" else "\u25d1"
        self._make_action_icon("toggle_ui_theme", ui_icon, i18n.t("tooltip.toggle_ui_theme"), self._top_container)

        # Bottom: ?
        self._bottom_container = tk.Frame(self.frame, bg=colors["sidebar"])
        self._bottom_container.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 8))
        self._make_action_icon("help", "?", i18n.t("tooltip.help"), self._bottom_container)

    def set_enabled(self, name: str, enabled: bool):
        lbl = self._action_icons.get(name)
        if not lbl: return
        
        colors = self._ctx.colors
        if enabled:
            lbl.config(fg=colors["secondary"], cursor="hand2")
            lbl.bind("<Button-1>", lambda e: self._commands[name]())
        else:
            lbl.config(fg=colors["border"], cursor="") # Using border color as 'disabled' look
            lbl.unbind("<Button-1>")

    def _make_action_icon(self, name: str, icon: str, tooltip: str, parent: tk.Widget):
        colors = self._ctx.colors
        cell = tk.Frame(parent, bg=colors["sidebar"], height=48, width=48)
        cell.pack(side=tk.TOP, fill=tk.X, pady=2)
        cell.pack_propagate(False)

        lbl = tk.Label(cell, text=icon, font=(FONT, 12, "bold"), bg=colors["sidebar"],
                       fg=colors["secondary"], cursor="hand2")
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        cmd = self._commands.get(name)
        if cmd:
            # Bind only to label to avoid duplicate command execution
            lbl.bind("<Button-1>", lambda e: cmd())

        for w in (cell, lbl):
            w.bind("<Enter>", lambda e: lbl.config(fg=colors["text_bright"]))
            w.bind("<Leave>", lambda e: lbl.config(fg=colors["secondary"]))

        if tooltip:
            Tooltip(cell, tooltip, colors)
            Tooltip(lbl, tooltip, colors)

        self._action_icons[name] = lbl
