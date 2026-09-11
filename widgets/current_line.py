"""Current-line highlight for the source editor.

Paints a background tag across the line holding the caret. The tag is kept at
the bottom of the priority stack so the selection and the search highlights
always win over it, and it only sets ``background`` so the Markdown syntax
colours (which set ``foreground``) are unaffected.
"""

from __future__ import annotations

import tkinter as tk

TAG = "current_line"


class CurrentLineHighlight:
    def __init__(self, text: tk.Text, color: str):
        self._text = text
        self._line = -1
        text.tag_configure(TAG, background=color)
        # Below everything: selection, search matches and syntax tags win.
        text.tag_lower(TAG)

    def set_color(self, color: str) -> None:
        try:
            self._text.tag_configure(TAG, background=color)
        except tk.TclError:
            pass

    def refresh(self, *_args) -> None:
        """Move the highlight to the caret's line. Cheap enough to call on
        every keystroke: it is a no-op while the caret stays on one line."""
        text = self._text
        try:
            if not text.winfo_exists():
                return
            line = int(text.index("insert").split(".")[0])
            ranges = text.tag_ranges(TAG)
            # Re-tag unless the tag already covers exactly this line: a
            # programmatic reload wipes every tag, and typing at column 0
            # pushes the range off the line start.
            if line == self._line and ranges and str(ranges[0]) == f"{line}.0":
                return
            text.tag_remove(TAG, "1.0", tk.END)
            text.tag_add(TAG, f"{line}.0", f"{line}.0 lineend+1c")
            text.tag_lower(TAG)
            self._line = line
        except tk.TclError:
            return

    def clear(self) -> None:
        try:
            self._text.tag_remove(TAG, "1.0", tk.END)
        except tk.TclError:
            pass
        self._line = -1
