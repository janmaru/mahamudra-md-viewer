from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from services.rd_parser import parse_rd
from widgets.rsvp_player import RsvpPlayer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rd_viewer",
        description="RSVP-style player for .rd description files.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Path to a .rd file. If omitted, a file dialog is opened.",
    )
    parser.add_argument(
        "--wpm",
        type=int,
        default=300,
        help="Initial words-per-minute (200..1200, default 300).",
    )
    args = parser.parse_args(argv)

    root = tk.Tk()
    root.title("rd_viewer — RSVP")
    root.geometry("900x500")
    root.minsize(640, 360)
    _apply_dark_theme(root)

    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(1, weight=1)

    title_var = tk.StringVar(value="(no file loaded)")
    header = ttk.Frame(container)
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
    header.columnconfigure(0, weight=1)
    ttk.Label(header, textvariable=title_var, font=("Segoe UI", 11)).grid(
        row=0, column=0, sticky="w"
    )
    ttk.Button(header, text="Open .rd…", command=lambda: _open_dialog(player, title_var)).grid(
        row=0, column=1, sticky="e"
    )

    player = RsvpPlayer(container, wpm=args.wpm)
    player.grid(row=1, column=0, sticky="nsew")

    initial = args.file
    if initial is not None:
        _load_file(player, title_var, initial)

    root.mainloop()
    return 0


def _open_dialog(player: RsvpPlayer, title_var: tk.StringVar) -> None:
    selected = filedialog.askopenfilename(
        title="Open .rd",
        filetypes=[("RD description", "*.rd"), ("All files", "*.*")],
    )
    if selected:
        _load_file(player, title_var, Path(selected))


def _load_file(player: RsvpPlayer, title_var: tk.StringVar, path: Path) -> None:
    try:
        sentences = parse_rd(path)
    except FileNotFoundError:
        messagebox.showerror("rd_viewer", f"File not found:\n{path}")
        return
    except OSError as exc:
        messagebox.showerror("rd_viewer", f"Cannot read file:\n{exc}")
        return

    if not sentences:
        messagebox.showwarning("rd_viewer", f"No readable text in:\n{path.name}")
        return

    title_var.set(f"{path.name}  ·  {len(sentences)} sentences")
    player.load(sentences)


def _apply_dark_theme(root: tk.Tk) -> None:
    root.configure(bg="#1e1e1e")
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", background="#1e1e1e", foreground="#d4d4d4", fieldbackground="#1e1e1e")
    style.configure("TFrame", background="#1e1e1e")
    style.configure("TLabel", background="#1e1e1e", foreground="#d4d4d4")
    style.configure(
        "TButton",
        background="#3c3c3c",
        foreground="#d4d4d4",
        borderwidth=0,
        focusthickness=0,
        padding=6,
    )
    style.map(
        "TButton",
        background=[("active", "#505050"), ("pressed", "#2d2d30")],
    )
    style.configure(
        "Horizontal.TScale",
        background="#1e1e1e",
        troughcolor="#3c3c3c",
    )


if __name__ == "__main__":
    sys.exit(main())
