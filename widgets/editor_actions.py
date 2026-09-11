"""Bridges the Edit menu / shortcuts to the active tab's ``tk.Text`` editor.

All transformations are delegated to the pure functions in
``services.md_editing``; this class only deals with Tk indices, selection
and undo grouping (``Text.replace`` is a single undo step).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable, Optional

from services import md_editing as edit
from services.md_highlighter import is_inside_fence

if TYPE_CHECKING:
    from app_context import AppContext


class EditorActions:
    def __init__(self, ctx: AppContext):
        self._ctx = ctx

    # ---------------------------------------------------------------- targets
    def _target(self) -> Optional[tk.Text]:
        tab = self._ctx.current_tab
        if tab is None or tab.source_text is None:
            return None
        if tab.pdf_viewer is not None or tab.rsvp_player is not None:
            return None
        if tab.read_only or tab.view_mode == "preview":
            return None
        return tab.source_text

    def can_edit(self) -> bool:
        return self._target() is not None

    def can_edit_from_shortcut(self) -> bool:
        """Global-shortcut guard: the editor is visible and the keyboard focus
        is not in a text-entry widget (e.g. the search box), which owns the
        keystroke."""
        t = self._target()
        if t is None:
            return False
        try:
            focus = self._ctx.root.focus_get()
        except (KeyError, tk.TclError):
            focus = None
        return not isinstance(focus, (tk.Entry, ttk.Entry, tk.Spinbox)) or focus is t

    # ------------------------------------------------------------- clipboard
    def undo(self) -> None:
        t = self._target()
        if t is None:
            return
        try:
            t.edit_undo()
        except tk.TclError:
            pass
        self._finish(t)

    def redo(self) -> None:
        t = self._target()
        if t is None:
            return
        try:
            t.edit_redo()
        except tk.TclError:
            pass
        self._finish(t)

    def cut(self) -> None:
        self._virtual("<<Cut>>")

    def copy(self) -> None:
        self._virtual("<<Copy>>")

    def paste(self) -> None:
        self._virtual("<<Paste>>")

    def select_all(self) -> None:
        t = self._target()
        if t is None:
            return
        t.tag_remove("sel", "1.0", tk.END)
        t.tag_add("sel", "1.0", "end-1c")
        t.mark_set("insert", "end-1c")
        t.focus_set()

    def _virtual(self, event: str) -> None:
        t = self._target()
        if t is None:
            return
        t.focus_set()
        t.event_generate(event)
        self._finish(t)

    # ------------------------------------------------------------ formatting
    def bold(self) -> None:
        self._wrap("**", self._ph("editor.placeholder_bold"))

    def italic(self) -> None:
        self._wrap("*", self._ph("editor.placeholder_italic"))

    def inline_code(self) -> None:
        self._wrap("`", self._ph("editor.placeholder_code"))

    def code_block(self) -> None:
        t = self._target()
        if t is None:
            return
        start, end = self._selection(t)
        selected = t.get(start, end)
        result = edit.wrap_code_block(selected, self._ph("editor.placeholder_code"))
        # Fences need their own lines: pad when the selection is inline.
        prefix = "" if t.compare(start, "==", f"{start} linestart") else "\n"
        suffix = "" if t.compare(end, "==", f"{end} lineend") else "\n"
        result = edit.EditResult(prefix + result.text + suffix,
                                 result.sel_start + len(prefix),
                                 result.sel_end + len(prefix))
        self._apply(t, start, end, result)

    def link(self) -> None:
        t = self._target()
        if t is None:
            return
        start, end = self._selection(t)
        selected = t.get(start, end)
        result = edit.make_link(selected, self._ph("editor.placeholder_link_text"),
                                self._ph("editor.placeholder_url"))
        self._apply(t, start, end, result)

    def heading(self, level: int) -> None:
        t = self._target()
        if t is None:
            return
        start, _end = self._selection(t)
        line_start = t.index(f"{start} linestart")
        line_end = t.index(f"{start} lineend")
        result = edit.set_heading(t.get(line_start, line_end), level)
        self._apply(t, line_start, line_end, result, select=False)

    # ----------------------------------------------------------- indentation
    def indent(self) -> bool | None:
        """Tab: indent the selected lines, or insert spaces up to the next tab
        stop. Never inserts a literal tab character.

        Returns None when there is no editable surface, which tells the
        binding to swallow the key rather than let Tk type into a hidden or
        read-only buffer; False means "declined, let Tk handle it"."""
        t = self._target()
        if t is None:
            return None
        if self._has_selection(t):
            self._lines(edit.indent_block)
            return True
        column = int(t.index("insert").split(".")[1])
        t.edit_separator()
        t.insert("insert", edit.spaces_to_tab_stop(column))
        t.edit_separator()
        self._finish(t)
        return True

    def outdent(self) -> bool | None:
        """Shift+Tab: remove one indent level from the selected lines, or the
        whitespace left of the caret. None when there is no editable surface."""
        t = self._target()
        if t is None:
            return None
        if self._has_selection(t):
            self._lines(lambda block: edit.outdent_block(block))
            return True
        prefix = t.get("insert linestart", "insert")
        count = edit.outdent_before_caret(prefix)
        if count:
            t.edit_separator()
            t.delete(f"insert -{count}c", "insert")
            t.edit_separator()
        self._finish(t)
        return True

    def newline(self) -> bool | None:
        """Enter: continue the current list, task or quote item. Returns False
        on an ordinary line so Tk inserts the newline itself, and None when
        there is no editable surface so the key is swallowed instead."""
        t = self._target()
        if t is None:
            return None
        line = t.get("insert linestart", "insert lineend")
        cont = edit.continue_list(line)
        if cont is None:
            return False
        # Inside a fenced code block "- x" is code, not a list item. Only
        # scanned when the line already looks like one, so prose pays nothing.
        line_no = int(t.index("insert").split(".")[0])
        if is_inside_fence(t.get("1.0", "end-1c").split("\n"), line_no):
            return False
        # Inside a fenced code block "- x" is code, not a list item. Only
        # scanned when the line already looks like one, so prose pays nothing.
        line_no = int(t.index("insert").split(".")[0])
        if is_inside_fence(t.get("1.0", "end-1c").split("\n"), line_no):
            return False
        t.edit_separator()
        if cont.clear_line:
            # Enter on an empty item ends the list instead of adding another.
            t.delete("insert linestart", "insert lineend")
        else:
            if self._has_selection(t):
                t.delete("sel.first", "sel.last")
            t.insert("insert", cont.text)
        t.edit_separator()
        self._finish(t)
        return True

    def bullet_list(self) -> None:
        self._lines(lambda block: edit.toggle_line_prefix(block, "- "))

    def numbered_list(self) -> None:
        self._lines(edit.toggle_numbered_list)

    def quote(self) -> None:
        self._lines(lambda block: edit.toggle_line_prefix(block, "> "))

    # --------------------------------------------------------------- helpers
    def _ph(self, key: str) -> str:
        i18n = self._ctx.i18n
        return i18n.t(key) if i18n else key

    @staticmethod
    def _has_selection(t: tk.Text) -> bool:
        try:
            return bool(t.tag_ranges("sel")) and t.compare("sel.first", "!=", "sel.last")
        except tk.TclError:
            return False

    @staticmethod
    def _selection(t: tk.Text) -> tuple[str, str]:
        try:
            return t.index("sel.first"), t.index("sel.last")
        except tk.TclError:
            pos = t.index("insert")
            return pos, pos

    def _wrap(self, marker: str, placeholder: str) -> None:
        t = self._target()
        if t is None:
            return
        start, end = self._selection(t)
        result = edit.toggle_wrap(t.get(start, end), marker, placeholder)
        self._apply(t, start, end, result)

    def _lines(self, fn: Callable[[str], edit.EditResult]) -> None:
        t = self._target()
        if t is None:
            return
        start, end = self._selection(t)
        line_start = t.index(f"{start} linestart")
        # A selection ending at column 0 should not drag the next line in.
        if t.compare(end, ">", start) and t.compare(end, "==", f"{end} linestart"):
            end = t.index(f"{end} -1c")
        line_end = t.index(f"{end} lineend")
        result = fn(t.get(line_start, line_end))
        self._apply(t, line_start, line_end, result)

    def _apply(self, t: tk.Text, start: str, end: str, result: edit.EditResult,
               select: bool = True) -> None:
        t.edit_separator()
        t.replace(start, end, result.text)
        t.edit_separator()
        sel_start = t.index(f"{start} +{result.sel_start}c")
        sel_end = t.index(f"{start} +{result.sel_end}c")
        t.tag_remove("sel", "1.0", tk.END)
        if select and result.sel_end > result.sel_start:
            t.tag_add("sel", sel_start, sel_end)
        t.mark_set("insert", sel_end)
        self._finish(t)

    @staticmethod
    def _finish(t: tk.Text) -> None:
        t.focus_set()
        t.see("insert")
        # Tell the gutter and the current-line highlight the caret moved.
        try:
            t.event_generate("<<CaretMoved>>", when="tail")
        except tk.TclError:
            pass
