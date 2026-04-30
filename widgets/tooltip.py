from __future__ import annotations

import tkinter as tk

from constants import FONT


class Tooltip:
    """Generic hover tooltip for any Tk widget."""

    def __init__(self, widget: tk.Widget, text: str, colors: dict,
                 delay_ms: int = 450, offset_x: int = 8, offset_y: int = 0):
        self._widget = widget
        self._text = text
        self._colors = colors
        self._delay_ms = delay_ms
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._after_id: str | None = None
        self._tip: tk.Toplevel | None = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self._widget.after(self._delay_ms, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self._widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self):
        if self._tip is not None or not self._text:
            return
        x = self._widget.winfo_rootx() + self._widget.winfo_width() + self._offset_x
        y = (self._widget.winfo_rooty()
             + (self._widget.winfo_height() // 2)
             + self._offset_y)
        tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.configure(bg=self._colors["border"])
        label = tk.Label(tw, text=self._text, background=self._colors["toolbar"],
                         foreground=self._colors["text"], font=(FONT, 9),
                         padx=8, pady=4, borderwidth=1, relief=tk.SOLID)
        label.pack()
        tw.update_idletasks()
        y -= tw.winfo_height() // 2
        tw.wm_geometry(f"+{x}+{y}")
        self._tip = tw

    def _hide(self, _event=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None

    def update_text(self, text: str):
        self._text = text
