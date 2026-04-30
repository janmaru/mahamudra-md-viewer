from __future__ import annotations

import tkinter as tk

from constants import FONT


class ListboxTooltip:
    """Shows a tooltip with the full path when hovering over listbox items."""

    def __init__(self, listbox, items_fn, colors: dict):
        self._listbox = listbox
        self._items_fn = items_fn
        self.colors = colors
        self._tip = None
        self._last_index = None
        listbox.bind("<Motion>", self._on_motion)
        listbox.bind("<Leave>", self._hide)

    def _on_motion(self, event):
        idx = self._listbox.nearest(event.y)
        if idx < 0 or idx >= len(self._items_fn()):
            self._hide()
            return
        if idx == self._last_index:
            return
        self._last_index = idx
        self._hide()
        path = self._items_fn()[idx]
        x = self._listbox.winfo_rootx() + event.x + 15
        y = self._listbox.winfo_rooty() + event.y + 10
        self._tip = tw = tk.Toplevel(self._listbox)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg=self.colors["border"])
        label = tk.Label(tw, text=str(path), background=self.colors["toolbar"],
                         foreground=self.colors["text"], font=(FONT, 9), padx=8, pady=4,
                         borderwidth=1, relief=tk.SOLID)
        label.pack()

    def _hide(self, event=None):
        if self._tip:
            self._tip.destroy()
            self._tip = None
        self._last_index = None
