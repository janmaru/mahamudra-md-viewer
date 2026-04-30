from __future__ import annotations

import tkinter as tk

from constants import FONT


class CustomMenu(tk.Toplevel):
    """A themed popup menu that matches the application's UI colors."""

    def __init__(self, master, items, colors):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=colors["border"])
        self.colors = colors

        container = tk.Frame(self, bg=colors["toolbar"], padx=1, pady=1)
        container.pack()

        for item in items:
            if item == "---":
                tk.Frame(container, bg=colors["border"], height=1).pack(fill=tk.X, pady=4)
                continue

            label_text, command = item
            lbl = tk.Label(container, text=f"  {label_text}  ", bg=colors["toolbar"],
                           fg=colors["text"], font=(FONT, 10), anchor=tk.W, padx=15, pady=6, cursor="hand2")
            lbl.pack(fill=tk.X)

            lbl.bind("<Button-1>", lambda e, cmd=command: self._execute(cmd))
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg=colors["list_active"], fg=colors["text_bright"]))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(bg=colors["toolbar"], fg=colors["text"]))

        self.bind("<FocusOut>", lambda e: self.destroy())
        self.after(10, self.focus_set)

    def _execute(self, command):
        self.destroy()
        if command:
            command()
