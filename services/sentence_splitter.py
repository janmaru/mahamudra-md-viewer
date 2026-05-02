from __future__ import annotations

import re

_ABBREVIATIONS = {
    "dr.", "mr.", "mrs.", "ms.", "prof.", "sig.", "sig.ra", "sigg.",
    "dott.", "dott.ssa", "ing.", "avv.", "rev.",
    "etc.", "vs.", "es.", "p.es.", "ca.", "n.", "nr.",
    "fig.", "cap.", "art.", "pag.", "pp.", "vol.",
    "i.e.", "e.g.",
}

_SENTENCE_END = re.compile(r"([.!?]+)(\s+|$)")


def split_sentences(text: str) -> list[str]:
    """Split *text* into sentences.

    Rough heuristic: break on `.!?` followed by whitespace, but skip if the
    token before the punctuation looks like a known abbreviation.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    sentences: list[str] = []
    start = 0
    pos = 0
    length = len(text)

    while pos < length:
        match = _SENTENCE_END.search(text, pos)
        if match is None:
            break

        end = match.end(1)
        candidate = text[start:end].strip()

        if _ends_with_abbreviation(candidate):
            pos = end
            continue

        if candidate:
            sentences.append(candidate)
        start = match.end()
        pos = start

    tail = text[start:].strip()
    if tail:
        sentences.append(tail)

    return sentences


def _ends_with_abbreviation(text: str) -> bool:
    lowered = text.lower()
    last_token = lowered.split()[-1] if lowered.split() else ""
    return last_token in _ABBREVIATIONS
