"""Line-number gutter for the source editor.

A thin ``tk.Canvas`` packed to the left of the editor ``tk.Text``. It draws one
number per *logical* line, positioned with ``Text.dlineinfo`` so a wrapped line
keeps a single number aligned with its first display row. Redraws are coalesced
through ``after_idle`` because the triggers (typing, scrolling, resizing) can
fire many times per interaction.

The widget owns no state beyond its geometry: the editor remains the single
source of truth.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional


class LineNumbers(tk.Canvas):
    PAD_X = 8       # space between the numbers and the editor text
    MIN_DIGITS = 2  # keep a stable width for short documents

    def __init__(self, parent: tk.Widget, text: tk.Text, colors: dict[str, str],
                 font_family: str, font_size: int):
        super().__init__(parent, bg=colors["bg"], highlightthickness=0, borderwidth=0,
                         takefocus=0)
        self._text = text
        self._colors = colors
        self._family = font_family
        self._size = font_size
        self._pending = False
        self._current_line = -1
        self._char_w: Optional[int] = None

        self.bind("<Configure>", lambda e: self.schedule())
        # A click in the gutter puts the caret on that line.
        self.bind("<Button-1>", self._on_click)
        self._apply_width()

    # ------------------------------------------------------------------ setup
    def set_font_size(self, size: int) -> None:
        if size == self._size:
            return
        self._size = size
        self._char_w = None
        self._apply_width()
        self.schedule()

    def _font(self) -> tuple[str, int]:
        # One point smaller than the editor: present, but not competing with it.
        return (self._family, max(7, self._size - 1))

    def _digits(self) -> int:
        try:
            total = int(self._text.index("end-1c").split(".")[0])
        except tk.TclError:
            total = 1
        return max(self.MIN_DIGITS, len(str(total)))

    def _char_width(self) -> int:
        """Width of a digit in the gutter font, measured once per font size."""
        if self._char_w is None:
            from tkinter import font as tkfont
            try:
                self._char_w = tkfont.Font(font=self._font()).measure("0")
            except tk.TclError:
                self._char_w = max(6, self._size)
        return self._char_w

    def _apply_width(self) -> None:
        self.configure(width=self._digits() * self._char_width() + self.PAD_X * 2)

    # -------------------------------------------------------------- scheduling
    def schedule(self) -> None:
        """Request a redraw; repeated calls in the same idle cycle collapse."""
        if self._pending:
            return
        self._pending = True
        try:
            self.after_idle(self.redraw)
        except tk.TclError:
            self._pending = False

    def on_scroll(self, *_args) -> None:
        self.schedule()

    # ------------------------------------------------------------------ paint
    def redraw(self) -> None:
        self._pending = False
        try:
            if not self.winfo_exists() or not self._text.winfo_exists():
                return
            self.delete("all")
            self._apply_width()
            # Use the width the canvas will have, not the stale one: when the
            # digit count grows, winfo_width() is still a frame behind.
            width = max(self.winfo_width(), int(self.cget("width")))
            try:
                current = int(self._text.index("insert").split(".")[0])
            except tk.TclError:
                current = -1

            height = max(1, self.winfo_height())
            first = int(self._text.index("@0,0").split(".")[0])
            last = int(self._text.index(f"@0,{height}").split(".")[0])
            total = int(self._text.index("end-1c").split(".")[0])
            for line in range(first, min(last, total) + 1):
                # Always measure the *start* of the logical line: with
                # wrap="word" an index carrying a column lands on a
                # continuation row and would misplace the number.
                info = self._text.dlineinfo(f"{line}.0")
                if info is None:
                    # Only reachable for the topmost line, whose first row is
                    # scrolled above the viewport: pin its number to the top.
                    if line != first:
                        continue
                    y = 0
                else:
                    y = info[1]
                self.create_text(
                    width - self.PAD_X, y,
                    anchor="ne", text=str(line),
                    font=self._font(),
                    fill=self._colors["text_bright"] if line == current else self._colors["secondary"])
        except tk.TclError:
            return

    # ------------------------------------------------------------------ input
    def _on_click(self, event) -> Optional[str]:
        if str(self._text.cget("state")) == "disabled":
            return None
        try:
            self._text.mark_set("insert", f"@0,{event.y} linestart")
            self._text.focus_set()
            self._text.event_generate("<<CaretMoved>>", when="tail")
        except tk.TclError:
            return None
        return "break"
