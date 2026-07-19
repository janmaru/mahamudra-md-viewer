"""Use case: Persist a tab's source text to disk.

Handles two flows:
- save(): overwrite the existing file on disk.
- save_as(): ask the user for a destination path, then write.

For untitled tabs (created via "New Markdown"), save() defers to save_as()
because there is no path yet.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app_context import AppContext, TabInfo


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
            initial_dir = str(ctx.scan_dir)
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
        content = tab.source_text.get("1.0", "end-1c")
        try:
            path.write_text(content, encoding="utf-8", newline="\n")
        except OSError:
            return False
        return True
