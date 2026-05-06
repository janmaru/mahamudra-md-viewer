"""
Hash-based disk cache for rendered diagrams.
Stores base64-encoded PNGs keyed by SHA-256 of the source code,
organized in subdirectories by source document name.
Shared by the diagram renderers.
"""

import hashlib
import shutil
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    _CACHE_DIR = Path(sys.executable).resolve().parent / ".diagram_cache"
else:
    _CACHE_DIR = Path(__file__).resolve().parent.parent / ".diagram_cache"

# Current document name, set by the caller before rendering
_current_doc: str = "_unknown"


def set_document(file_path: str | Path) -> None:
    """Set the current document name for cache organization."""
    global _current_doc
    _current_doc = Path(file_path).stem


def _doc_dir() -> Path:
    return _CACHE_DIR / _current_doc


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def get(code: str) -> str | None:
    """Return cached base64 PNG for the given diagram code, or None."""
    key = _hash_code(code)
    cache_file = _doc_dir() / f"{key}.b64"
    if cache_file.exists():
        return cache_file.read_text(encoding="ascii")
    return None


def put(code: str, png_b64: str) -> None:
    """Store base64 PNG in cache."""
    doc_dir = _doc_dir()
    doc_dir.mkdir(parents=True, exist_ok=True)
    key = _hash_code(code)
    cache_file = doc_dir / f"{key}.b64"
    cache_file.write_text(png_b64, encoding="ascii")


def clear(doc_name: str | None = None) -> None:
    """Remove cached diagrams. If doc_name is given, clear only that document's cache."""
    if doc_name:
        doc_dir = _CACHE_DIR / doc_name
        if doc_dir.exists():
            shutil.rmtree(doc_dir)
    elif _CACHE_DIR.exists():
        shutil.rmtree(_CACHE_DIR)
