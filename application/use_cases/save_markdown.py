"""Use case: Persist a tab's source text to disk.

Handles two flows:
- save(): overwrite the existing file on disk.
- save_as(): ask the user for a destination path, then write.

For untitled tabs (created via "New Markdown"), save() defers to save_as()
because there is no path yet.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app_context import AppContext, TabInfo


def _replace_preserving_metadata(tmp_path: str, path: Path) -> None:
    """Move ``tmp_path`` onto ``path``, keeping the target's metadata.

    On Windows ``ReplaceFileW`` is the documented way to swap a file while
    preserving its ACLs, attributes and creation time; ``os.replace`` would
    hand the new file the temporary's security descriptor, silently dropping
    any explicit permission granted on the document. Everywhere else (and
    whenever the API refuses, e.g. some network shares) the POSIX pair
    ``copymode`` + ``os.replace`` is used.
    """
    if sys.platform == "win32" and path.exists():
        import ctypes
        from ctypes import wintypes

        REPLACEFILE_IGNORE_MERGE_ERRORS = 0x00000002
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.ReplaceFileW.argtypes = [
                wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID]
            kernel32.ReplaceFileW.restype = wintypes.BOOL
            if kernel32.ReplaceFileW(str(path), tmp_path, None,
                                     REPLACEFILE_IGNORE_MERGE_ERRORS, None, None):
                return
        except (OSError, AttributeError):
            pass  # fall back to the portable path below

    if path.exists():
        try:
            shutil.copymode(path, tmp_path)
        except OSError:
            pass  # unsupported filesystem: keep the default mode
    os.replace(tmp_path, path)


class SaveMarkdownUseCase:
    def save(self, tab: TabInfo) -> bool:
        if tab.source_text is None:
            return False
        if tab.is_untitled:
            return False
        return self._write(tab, tab.path)

    def save_as(self, ctx: AppContext, tab: TabInfo) -> Optional[Path]:
        if tab.source_text is None:
            return None
        if tab.is_untitled:
            initial_name = f"{tab.path.stem}.md"
            # A tab recreated from a file that disappeared keeps its absolute
            # path: offer its original folder rather than the scan root.
            parent = tab.path.parent
            initial_dir = str(parent if parent.is_absolute() and parent.is_dir() else ctx.scan_dir)
        else:
            initial_name = tab.path.name
            initial_dir = str(tab.path.parent)

        path_str = filedialog.asksaveasfilename(
            defaultextension=".md",
            initialfile=initial_name,
            initialdir=initial_dir,
            filetypes=[
                ("Markdown", "*.md *.markdown *.mdown *.mkd"),
                ("All files", "*.*"),
            ],
        )
        if not path_str:
            return None
        new_path = Path(path_str)
        if not self._write(tab, new_path):
            return None
        return new_path

    def _write(self, tab: TabInfo, path: Path) -> bool:
        """Write the buffer through a temporary file in the destination folder,
        flushed to disk, then renamed over the target. An interrupted or failed
        write therefore leaves the previous version intact instead of a
        truncated file. The temporary file shares the folder so the rename
        stays on one filesystem, which is what makes the swap atomic; the
        directory entry itself is not fsync'd, so a power loss can still lose
        the rename (acceptable for a desktop editor).

        The target's permissions are carried over to the replacement,
        otherwise every save would reset them to the temporary file's."""
        content = tab.source_text.get("1.0", "end-1c")
        tmp_path: Optional[str] = None
        try:
            # Cap the prefix: name + random suffix must stay inside the
            # filesystem's component limit, or long names could not be saved.
            with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", newline="\n", delete=False,
                    dir=str(path.parent), prefix=f".{path.name[:60]}.", suffix=".tmp") as tmp:
                tmp_path = tmp.name
                tmp.write(content)
                tmp.flush()
                os.fsync(tmp.fileno())
            _replace_preserving_metadata(tmp_path, path)
            return True
        except OSError:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            return False
