from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InlineSpan:
    """A piece of text with optional inline emphasis."""
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


@dataclass(frozen=True)
class Sentence:
    """A sentence parsed from a `.rd` file, made of inline spans."""
    spans: tuple[InlineSpan, ...]

    @property
    def plain(self) -> str:
        return "".join(span.text for span in self.spans)

    @property
    def word_count(self) -> int:
        return len(self.plain.split())


_PREFIX_RE = re.compile(r"^\s*(?:#{1,6}\s+|>\s?|[-*+]\s+|\d+\.\s+)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_INLINE_TOKEN = re.compile(r"(\*\*|__|\*|_|`)")


def parse_rd(path: Path | str) -> list[Sentence]:
    """Parse a `.rd` file: one non-empty line = one sentence.

    Empty lines are ignored. Each line is stripped of trivial block-Markdown
    prefixes (header `#`, blockquote `>`, list bullets) and parsed for inline
    emphasis (`**bold**`, `*italic*`, ``code``).
    """
    raw = Path(path).read_text(encoding="utf-8")
    sentences: list[Sentence] = []
    for line in raw.splitlines():
        cleaned = _clean_line(line)
        if not cleaned:
            continue
        sentences.append(Sentence(spans=_parse_inline(cleaned)))
    return sentences


def _clean_line(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    line = _PREFIX_RE.sub("", line, count=1)
    line = _IMAGE_RE.sub("", line)
    line = _LINK_RE.sub(r"\1", line)
    line = _HTML_TAG_RE.sub("", line)
    return line.strip()


def _parse_inline(text: str) -> tuple[InlineSpan, ...]:
    """Convert inline markdown (`**bold**`, `*italic*`, ``code``) into spans."""
    spans: list[InlineSpan] = []
    bold = False
    italic = False
    code = False
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            spans.append(InlineSpan(
                text="".join(buffer),
                bold=bold,
                italic=italic,
                code=code,
            ))
            buffer.clear()

    pos = 0
    length = len(text)
    while pos < length:
        match = _INLINE_TOKEN.search(text, pos)
        if match is None:
            buffer.append(text[pos:])
            break

        if match.start() > pos:
            buffer.append(text[pos:match.start()])

        token = match.group(1)

        if code:
            if token == "`":
                flush()
                code = False
            else:
                buffer.append(token)
        elif token == "`":
            flush()
            code = True
        elif token in ("**", "__"):
            flush()
            bold = not bold
        elif token in ("*", "_"):
            flush()
            italic = not italic
        else:
            buffer.append(token)

        pos = match.end()

    flush()
    return tuple(spans) if spans else (InlineSpan(text=text),)
