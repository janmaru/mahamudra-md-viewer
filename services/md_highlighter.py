"""Markdown syntax highlighting for the source editor.

Two layers:

- ``tokenize()`` is a pure function: it scans a list of lines and returns
  ``Token`` records (tag, line, start column, end column). It is Tk-free so
  it can be unit-tested in isolation.
- ``MarkdownHighlighter`` binds a ``tk.Text`` widget: it debounces edits and
  scroll events, then re-applies tags only on the visible window (plus a
  margin), so large documents stay responsive. Fenced-code state is tracked
  from the top of the document so a fence opened above the viewport is still
  honoured.
"""

from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Iterable, Optional


@dataclass(frozen=True)
class Token:
    tag: str
    line: int   # 1-based, matches tk.Text line indexing
    start: int  # 0-based column, inclusive
    end: int    # 0-based column, exclusive


TAGS = (
    "md_heading", "md_bold", "md_italic", "md_code", "md_code_block",
    "md_fence", "md_link", "md_url", "md_image", "md_list", "md_quote",
    "md_hr", "md_table", "md_html",
)

_FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?:\s|$)")
_HR_RE = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
_QUOTE_RE = re.compile(r"^\s{0,3}(?:>\s?)+")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])(?=\s)")
_TABLE_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_PIPE_RE = re.compile(r"\|")

_CODE_RE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)")
_BOLD_RE = re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1")
_ITALIC_RE = re.compile(r"(?<![*\w])(\*|_)(?=[^\s*_])([^*_]+?)(?<=\S)\1(?![*\w])")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)[^)]*\)")
_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)[^)]*\)")
_HTML_RE = re.compile(r"</?[A-Za-z][^<>]*>")


def is_inside_fence(lines: list[str], line_no: int) -> bool:
    """True when the 1-based ``line_no`` sits inside a fenced code block.

    Shares the fence rules used by :func:`tokenize`: a closing fence must use
    the same marker family and be at least as long as the opening one. The
    opening fence line itself is *not* inside; the lines after it are.
    """
    in_fence = False
    marker = ""
    for text in lines[:max(0, line_no - 1)]:
        match = _FENCE_RE.match(text)
        if match is None:
            continue
        if in_fence:
            if (match.group(1)[0] == marker[0]
                    and len(match.group(1)) >= len(marker)
                    and text.strip() == match.group(1)):
                in_fence = False
                marker = ""
        else:
            in_fence = True
            marker = match.group(1)
    return in_fence


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < e and end > s for s, e in spans)


def _inline_tokens(line_no: int, text: str) -> Iterable[Token]:
    # Code spans first: they shield their content from every other rule.
    protected: list[tuple[int, int]] = []
    for m in _CODE_RE.finditer(text):
        protected.append((m.start(), m.end()))
        yield Token("md_code", line_no, m.start(), m.end())

    for m in _IMAGE_RE.finditer(text):
        if _overlaps(m.start(), m.end(), protected):
            continue
        protected.append((m.start(), m.end()))
        yield Token("md_image", line_no, m.start(), m.end())
        yield Token("md_url", line_no, m.start(1), m.end(1))

    for m in _LINK_RE.finditer(text):
        if _overlaps(m.start(), m.end(), protected):
            continue
        protected.append((m.start(), m.end()))
        yield Token("md_link", line_no, m.start(), m.end())
        yield Token("md_url", line_no, m.start(1), m.end(1))

    for m in _HTML_RE.finditer(text):
        if _overlaps(m.start(), m.end(), protected):
            continue
        protected.append((m.start(), m.end()))
        yield Token("md_html", line_no, m.start(), m.end())

    bold_spans: list[tuple[int, int]] = []
    for m in _BOLD_RE.finditer(text):
        if _overlaps(m.start(), m.end(), protected):
            continue
        bold_spans.append((m.start(), m.end()))
        yield Token("md_bold", line_no, m.start(), m.end())

    for m in _ITALIC_RE.finditer(text):
        if _overlaps(m.start(), m.end(), protected):
            continue
        if _overlaps(m.start(), m.end(), bold_spans):
            continue
        yield Token("md_italic", line_no, m.start(), m.end())


def tokenize(lines: list[str], first: int = 1, last: Optional[int] = None) -> list[Token]:
    """Return highlight tokens for lines ``first``..``last`` (1-based, inclusive).

    Every line from the top is scanned for fence markers so the code-block
    state is correct for the requested window; only lines inside the window
    produce tokens.
    """
    if last is None or last > len(lines):
        last = len(lines)
    first = max(1, first)

    tokens: list[Token] = []
    in_fence = False
    fence_marker = ""

    for idx, text in enumerate(lines, start=1):
        fence_match = _FENCE_RE.match(text)
        if in_fence:
            closes = bool(fence_match) and fence_match.group(1)[0] == fence_marker[0] \
                and len(fence_match.group(1)) >= len(fence_marker) \
                and text.strip() == fence_match.group(1)
            if first <= idx <= last:
                tag = "md_fence" if closes else "md_code_block"
                if text:
                    tokens.append(Token(tag, idx, 0, len(text)))
            if closes:
                in_fence = False
                fence_marker = ""
            continue

        if fence_match:
            in_fence = True
            fence_marker = fence_match.group(1)
            if first <= idx <= last and text:
                tokens.append(Token("md_fence", idx, 0, len(text)))
            continue

        if idx < first or idx > last or not text:
            continue

        if _HR_RE.match(text):
            tokens.append(Token("md_hr", idx, 0, len(text)))
            continue

        if _HEADING_RE.match(text):
            tokens.append(Token("md_heading", idx, 0, len(text)))
            tokens.extend(_inline_tokens(idx, text))
            continue

        quote = _QUOTE_RE.match(text)
        if quote:
            tokens.append(Token("md_quote", idx, 0, len(text)))
            tokens.extend(_inline_tokens(idx, text))
            continue

        lst = _LIST_RE.match(text)
        if lst:
            tokens.append(Token("md_list", idx, lst.start(), lst.end()))

        if _TABLE_RE.match(text):
            for pipe in _TABLE_PIPE_RE.finditer(text):
                tokens.append(Token("md_table", idx, pipe.start(), pipe.end()))

        tokens.extend(_inline_tokens(idx, text))

    return tokens


class MarkdownHighlighter:
    """Applies Markdown syntax tags to a ``tk.Text`` widget.

    The widget owns the content; this class only manages tags. It re-runs on
    ``<<Modified>>`` (fired by both typing and programmatic inserts),
    ``<Configure>`` (resize) and whenever ``on_scroll`` is invoked by the
    owner's ``yscrollcommand`` wrapper.
    """

    def __init__(self, text: tk.Text, palette: dict[str, str], font_family: str,
                 font_size: int, delay_ms: int = 150, margin_lines: int = 100):
        self._text = text
        self._palette = palette
        self._family = font_family
        self._size = font_size
        self._delay = delay_ms
        self._margin = margin_lines
        self._job: Optional[str] = None
        self._enabled = True

        self._configure_tags()
        text.bind("<<Modified>>", lambda e: self.schedule(), add="+")
        text.bind("<Configure>", lambda e: self.schedule(), add="+")

    # ------------------------------------------------------------------ setup
    def _configure_tags(self) -> None:
        base = (self._family, self._size)
        bold = (self._family, self._size, "bold")
        italic = (self._family, self._size, "italic")
        fonts = {
            "md_heading": bold,
            "md_bold": bold,
            "md_italic": italic,
            "md_quote": italic,
        }
        for tag in TAGS:
            opts = {"foreground": self._palette.get(tag, "")}
            font = fonts.get(tag)
            if font:
                opts["font"] = font
            self._text.tag_configure(tag, **opts)
            self._text.tag_lower(tag)
        # Priority inside the syntax layer: inline tags above block tags so a
        # code span or link inside a heading / quote keeps its own colour.
        # Search tags only set ``background`` and syntax tags only set
        # ``foreground`` / ``font``, so the two layers never compete.
        for tag in ("md_bold", "md_italic", "md_code", "md_link", "md_image", "md_url", "md_html"):
            self._text.tag_raise(tag)
        self._text.tag_raise("md_url")

    def set_font_size(self, size: int) -> None:
        if size == self._size:
            return
        self._size = size
        self._configure_tags()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self.cancel()
            for tag in TAGS:
                self._text.tag_remove(tag, "1.0", tk.END)
        else:
            self.schedule()

    # -------------------------------------------------------------- scheduling
    def cancel(self) -> None:
        """Drop a pending highlight job (call before the widget is destroyed)."""
        if self._job is not None:
            try:
                self._text.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def schedule(self) -> None:
        if not self._enabled:
            return
        self.cancel()
        try:
            self._job = self._text.after(self._delay, self.highlight_visible)
        except tk.TclError:
            self._job = None

    def on_scroll(self, *_args) -> None:
        self.schedule()

    # ---------------------------------------------------------------- highlight
    def highlight_visible(self) -> None:
        self._job = None
        if not self._enabled:
            return
        text = self._text
        try:
            if not text.winfo_exists():
                return
            first_visible = int(text.index("@0,0").split(".")[0])
            height = max(1, text.winfo_height())
            last_visible = int(text.index(f"@0,{height}").split(".")[0])
            content = text.get("1.0", "end-1c")
        except tk.TclError:
            return

        lines = content.split("\n")
        first = max(1, first_visible - self._margin)
        last = min(len(lines), last_visible + self._margin)
        if last < first:
            return

        for tag in TAGS:
            text.tag_remove(tag, f"{first}.0", f"{last}.end")
        for tok in tokenize(lines, first, last):
            text.tag_add(tok.tag, f"{tok.line}.{tok.start}", f"{tok.line}.{tok.end}")
