from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import sys

from constants import APP_DIR

if TYPE_CHECKING:
    import tkinter as tk
    from app_context import AppContext

# In frozen mode, store settings next to the .exe (writable), not inside the bundle
if getattr(sys, "frozen", False):
    _SETTINGS_DIR = Path(sys.executable).resolve().parent
else:
    _SETTINGS_DIR = APP_DIR

SETTINGS_FILE = _SETTINGS_DIR / "settings.json"


def load_settings(ctx: AppContext) -> str | None:
    """Load settings into ctx. Returns window geometry string or None."""
    if not SETTINGS_FILE.exists():
        return "1200x800"
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return "1200x800"

    ctx.ui_theme = data.get("ui_theme", "dark")

    geo = data.get("window_geometry", "1200x800")

    folder = data.get("last_folder")
    if folder:
        p = Path(folder)
        if p.is_dir():
            ctx.scan_dir = p

    last = data.get("last_file")
    if last:
        p = Path(last)
        if p.is_file():
            # We don't set it here directly because it's now a property 
            # and requires the UI to be ready for tabs. 
            # md_reader.py handles loading the initial file after UI build.
            pass

    ctx.recent_files = [
        Path(f) for f in data.get("recent_files", []) if Path(f).is_file()
    ]

    theme_name = data.get("theme")
    if theme_name and theme_name in ctx.themes:
        ctx.theme_index = ctx.theme_names.index(theme_name)
        ctx.css_path = ctx.themes[theme_name]

    return geo


def save_settings(ctx: AppContext) -> None:
    data = {
        "window_geometry": ctx.root.geometry(),
        "last_folder": str(ctx.scan_dir),
        "last_file": str(ctx.current_file) if ctx.current_file else None,
        "recent_files": [str(f) for f in ctx.recent_files],
        "theme": ctx.theme_names[ctx.theme_index] if ctx.theme_names else None,
        "ui_theme": ctx.ui_theme,
    }
    try:
        SETTINGS_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def ensure_on_screen(root: tk.Tk) -> None:
    try:
        import ctypes
        import ctypes.wintypes
        user32 = ctypes.windll.user32
        cx = root.winfo_x() + root.winfo_width() // 2
        cy = root.winfo_y() + root.winfo_height() // 2
        monitor = user32.MonitorFromPoint(ctypes.wintypes.POINT(cx, cy), 0)
        if not monitor:
            w = root.winfo_width()
            h = root.winfo_height()
            root.geometry(f"{w}x{h}+100+100")
    except Exception:
        pass
