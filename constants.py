from __future__ import annotations

import sys
from pathlib import Path

# PyInstaller stores data files in sys._MEIPASS when running as a bundle
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys._MEIPASS)
else:
    APP_DIR = Path(__file__).resolve().parent
STYLES_DIR = APP_DIR / "styles"

FONT = "Segoe UI"
FONT_MONO = "Consolas"

DARK_COLORS = {
    "titlebar": "#323233",
    "toolbar": "#252526",
    "bg": "#1e1e1e",
    "panel": "#252526",
    "sidebar": "#252526",
    "border": "#3c3c3c",
    "text": "#cccccc",
    "text_bright": "#d4d4d4",
    "secondary": "#858585",
    "accent": "#007acc",
    "link": "#3794ff",
    "hover": "#2a2d2e",
    "list_active": "#37373d",
    "selection": "#264f78",
    "statusbar": "#007acc",
    "statusbar_text": "#ffffff",
    "input_bg": "#3c3c3c",
    "badge": "#4d4d4d",
    "btn_hover": "#3c3c3c",
}

LIGHT_COLORS = {
    "titlebar": "#ffffff",
    "toolbar": "#ffffff",
    "bg": "#ffffff",
    "panel": "#fbfbfb",
    "sidebar": "#f6f6f6",
    "border": "#e8e8e8",
    "text": "#5c5c5c",
    "text_bright": "#222222",
    "secondary": "#999999",
    "accent": "#7c3aed", # Obsidian purple-ish accent
    "link": "#4f46e5",
    "hover": "#f3f4f6",
    "list_active": "#e5e7eb",
    "selection": "#dbeafe",
    "statusbar": "#f3f4f6",
    "statusbar_text": "#6b7280",
    "input_bg": "#ffffff",
    "badge": "#f3f4f6",
    "btn_hover": "#f9fafb",
}

ICONS = {
    ".md": "M\u2193",
    ".txt": "\u2261",
    ".py": "\u03bb",
    ".js": "JS",
    ".ts": "TS",
    ".json": "{}",
    ".yaml": "Y",
    ".yml": "Y",
    ".jpg": "\u25a3",
    ".jpeg": "\u25a3",
    ".png": "\u25a3",
    ".gif": "\u25a3",
    ".csv": "\u2637",
    ".log": "\u2630",
    ".pdf": "\u25a0",
    "folder": "\u25b8",
    "folder_open": "\u25be",
}


def discover_themes() -> dict[str, Path]:
    themes = {}
    if STYLES_DIR.is_dir():
        for css in sorted(STYLES_DIR.glob("*.css")):
            name = css.stem.replace("_", " ").replace("-", " ").title()
            themes[name] = css
    return themes


def get_version() -> str:
    v_file = APP_DIR / "VERSION"
    if v_file.exists():
        return v_file.read_text(encoding="utf-8").strip()
    return "1.0.0"
