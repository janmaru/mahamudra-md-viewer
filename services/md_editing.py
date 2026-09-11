"""Pure text transformations behind the editor's formatting commands.

Every function takes plain strings and returns an ``EditResult`` holding the
replacement text plus the selection (as offsets relative to the start of the
replacement) the editor should apply afterwards. No Tk dependency, so the
behaviour is unit-testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EditResult:
    text: str
    sel_start: int
    sel_end: int

    @classmethod
    def whole(cls, text: str) -> "EditResult":
        return cls(text, 0, len(text))


def toggle_wrap(selected: str, marker: str, placeholder: str) -> EditResult:
    """Wrap ``selected`` with ``marker`` on both sides, or unwrap it when it
    already carries the marker. An empty selection yields the wrapped
    ``placeholder`` with the placeholder itself selected."""
    if not selected:
        return EditResult(f"{marker}{placeholder}{marker}", len(marker), len(marker) + len(placeholder))
    n = len(marker)
    if len(selected) >= 2 * n and selected.startswith(marker) and selected.endswith(marker):
        inner = selected[n:-n]
        # "**bold**" toggled with "*" must nest (***bold***), not unwrap; and
        # "*a* and *b*" is two runs, not one wrapped span.
        if not (inner.startswith(marker[0]) or inner.endswith(marker[0])) and marker not in inner:
            return EditResult.whole(inner)
    return EditResult(f"{marker}{selected}{marker}", n, n + len(selected))


def toggle_line_prefix(block: str, prefix: str) -> EditResult:
    """Add ``prefix`` to every non-empty line of ``block``; if every non-empty
    line already starts with it (ignoring leading spaces), strip it instead."""
    lines = block.split("\n")
    if block == "":
        return EditResult(prefix, len(prefix), len(prefix))
    non_empty = [ln for ln in lines if ln.strip()]
    pattern = re.compile(r"^(\s*)" + re.escape(prefix))
    if not non_empty:
        # Only blank lines selected: give each one an empty item, keep the count.
        return EditResult.whole("\n".join(ln + prefix for ln in lines))
    all_prefixed = all(pattern.match(ln) for ln in non_empty)
    out = []
    for ln in lines:
        if not ln.strip():
            out.append(ln)
        elif all_prefixed:
            out.append(pattern.sub(r"\1", ln, count=1))
        elif pattern.match(ln):
            out.append(ln)  # already carries the prefix: leave it alone
        else:
            indent_len = len(ln) - len(ln.lstrip())
            out.append(ln[:indent_len] + prefix + ln[indent_len:])
    return EditResult.whole("\n".join(out))


_NUMBERED_RE = re.compile(r"^(\s*)\d+[.)](?=\s|$)\s*")  # "1.5 ratio" is prose, not a list


def toggle_numbered_list(block: str) -> EditResult:
    """Number every non-empty line (``1. ``, ``2. `` ...); if all of them are
    already numbered, remove the numbering."""
    lines = block.split("\n")
    if block == "":
        return EditResult("1. ", 3, 3)
    non_empty = [ln for ln in lines if ln.strip()]
    if not non_empty:
        return EditResult.whole("\n".join(f"{ln}{i}. " for i, ln in enumerate(lines, start=1)))
    all_numbered = all(_NUMBERED_RE.match(ln) for ln in non_empty)
    out = []
    counter = 0
    for ln in lines:
        if not ln.strip():
            out.append(ln)
        elif all_numbered:
            out.append(_NUMBERED_RE.sub(r"\1", ln, count=1))
        else:
            counter += 1
            indent_len = len(ln) - len(ln.lstrip())
            out.append(f"{ln[:indent_len]}{counter}. {ln[indent_len:]}")
    return EditResult.whole("\n".join(out))


_HEADING_RE = re.compile(r"^(\s{0,3})(#{1,6})\s+")


def set_heading(line: str, level: int) -> EditResult:
    """Make ``line`` a heading of ``level``. Applying the same level to a line
    that already has it removes the heading; a different level replaces it."""
    level = max(1, min(6, level))
    m = _HEADING_RE.match(line)
    if m:
        current = len(m.group(2))
        body = line[m.end():]
        if current == level:
            return EditResult.whole(m.group(1) + body)
        return EditResult.whole(f"{m.group(1)}{'#' * level} {body}")
    stripped = line.lstrip()
    indent = line[:len(line) - len(stripped)]
    return EditResult.whole(f"{indent}{'#' * level} {stripped}")


def make_link(selected: str, text_placeholder: str, url_placeholder: str) -> EditResult:
    """Build ``[text](url)``. With a selection, it becomes the link text and the
    URL placeholder is selected for immediate typing; without one, the text
    placeholder is selected."""
    if selected:
        prefix = f"[{selected}]("
        return EditResult(f"{prefix}{url_placeholder})", len(prefix), len(prefix) + len(url_placeholder))
    return EditResult(f"[{text_placeholder}]({url_placeholder})", 1, 1 + len(text_placeholder))


def wrap_code_block(selected: str, placeholder: str, lang: str = "") -> EditResult:
    """Wrap ``selected`` in a fenced code block, with the fences on their own
    lines and the body selected."""
    body = selected if selected else placeholder
    body = body.strip("\n")
    open_fence = f"```{lang}\n"
    text = f"{open_fence}{body}\n```"
    return EditResult(text, len(open_fence), len(open_fence) + len(body))


# --------------------------------------------------------------- indentation
INDENT_WIDTH = 4
INDENT = " " * INDENT_WIDTH


def spaces_to_tab_stop(column: int, width: int = INDENT_WIDTH) -> str:
    """Spaces needed to reach the next tab stop from ``column`` (0-based)."""
    return " " * (width - (column % width))


def indent_block(block: str, indent: str = INDENT) -> EditResult:
    """Indent every non-empty line of ``block`` by one level."""
    lines = block.split("\n")
    out = [ln if not ln.strip() else indent + ln for ln in lines]
    return EditResult.whole("\n".join(out))


def outdent_block(block: str, width: int = INDENT_WIDTH) -> EditResult:
    """Remove up to one indent level of leading whitespace from every line.
    A tab counts as a full level."""
    out = []
    for ln in block.split("\n"):
        if ln.startswith("\t"):
            out.append(ln[1:])
            continue
        removed = 0
        while removed < width and len(ln) > removed and ln[removed] == " ":
            removed += 1
        out.append(ln[removed:])
    return EditResult.whole("\n".join(out))


def outdent_before_caret(prefix: str, width: int = INDENT_WIDTH) -> int:
    """How many characters to delete to the left of the caret when
    out-denting with no selection. ``prefix`` is the line up to the caret;
    0 means there is nothing to remove."""
    if prefix.endswith("\t"):
        return 1
    if not prefix.endswith(" "):
        return 0
    spaces = len(prefix) - len(prefix.rstrip(" "))
    # Land on the previous tab stop rather than always eating a full level.
    step = len(prefix) % width or width
    return min(spaces, step)


# -------------------------------------------------------- list continuation
@dataclass(frozen=True)
class Continuation:
    """What pressing Enter should do on a list / quote line.

    ``clear_line`` means the item is empty and the marker must be removed
    instead of continued (this is how a list is ended). Otherwise ``text`` is
    inserted at the caret.
    """
    text: str
    clear_line: bool = False


# "- - -" and "* * *" are thematic breaks, not the start of a list.
_THEMATIC_BREAK_RE = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
_BULLET_RE = re.compile(r"^(\s*)([-*+])(\s+)(\[[ xX]\]\s+)?")
_ORDERED_RE = re.compile(r"^(\s*)(\d+)([.)])(\s+)(\[[ xX]\]\s+)?")
_QUOTE_CONT_RE = re.compile(r"^(\s*)((?:>\s?)+)")


def continue_list(line: str) -> Continuation | None:
    """Return what Enter should do on ``line``, or None when it is not a
    list, task or quote line (the caller then inserts a plain newline)."""
    if _THEMATIC_BREAK_RE.match(line):
        return None
    ordered = _ORDERED_RE.match(line)
    if ordered:
        indent, number, sep, space, box = ordered.groups()
        if not line[ordered.end():].strip():
            return Continuation("", clear_line=True)
        nxt = f"{indent}{int(number) + 1}{sep}{space}"
        return Continuation("\n" + nxt + ("[ ] " if box else ""))

    bullet = _BULLET_RE.match(line)
    if bullet:
        indent, marker, space, box = bullet.groups()
        if not line[bullet.end():].strip():
            return Continuation("", clear_line=True)
        return Continuation("\n" + f"{indent}{marker}{space}" + ("[ ] " if box else ""))

    quote = _QUOTE_CONT_RE.match(line)
    if quote:
        indent, marks = quote.groups()
        if not line[quote.end():].strip():
            return Continuation("", clear_line=True)
        return Continuation("\n" + indent + marks)

    return None
