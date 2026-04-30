from __future__ import annotations

import html as html_module
import os
import re
import subprocess
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

from services.css_loader import build_html
from services.diagram_cache import set_document as set_cache_document
from services.log_renderer import render_log
from services.file_renderer import CODE_EXTS

if TYPE_CHECKING:
    from app_context import AppContext
    from services.file_renderer import FileRenderer


def _find_msedge() -> str:
    standard_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in standard_paths:
        if os.path.exists(path):
            return path
    return "msedge"


def export_pdf(ctx: AppContext, renderer: FileRenderer) -> None:
    if not ctx.current_file:
        messagebox.showwarning("Export PDF", "No file is currently open.")
        return

    if ctx.current_file.suffix.lower() == ".pdf":
        ctx.show_toast(f"{ctx.i18n.t('error.export_failed')}: already a PDF", duration=3000)
        return

    dest_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile=ctx.current_file.stem + ".pdf"
    )
    if not dest_path:
        return

    if ctx.view_mode == "preview":
        ext = ctx.current_file.suffix.lower()
        try:
            content = ctx.current_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = ctx.current_file.read_text(encoding="latin-1")

        if ext == ".log":
            dark_bg = "dark" in (ctx.css_path.stem if ctx.css_path else "dark")
            html_body = render_log(content, dark_bg=dark_bg)
        elif ext == ".csv":
            html_body = renderer._render_csv(content)
        elif ext in CODE_EXTS:
            html_body = renderer._render_code(content, ext)
        elif ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"):
            html_body = renderer._render_image(ctx.current_file)
        else:
            set_cache_document(ctx.current_file)
            html_body = renderer._render_markdown(content, async_mermaid=False)
    else:
        content = ctx.source_text.get("1.0", tk.END)
        html_body = f'<pre style="padding:20px;white-space:pre-wrap;">{html_module.escape(content)}</pre>'

    # Strip diagram zoom links — PDF readers interpret them as real URIs
    html_body = re.sub(
        r'<a\s+href="diagram:[^"]*"[^>]*>(.*?)</a>',
        r'\1',
        html_body,
        flags=re.DOTALL,
    )
    html_body = html_body.replace('style="cursor:zoom-in"', '')

    base_url = ctx.current_file.parent.absolute().as_uri() + "/"
    full_html = build_html(html_body, ctx.css_path, base_url=base_url)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
        tf.write(full_html)
        temp_html = tf.name

    try:
        edge_path = _find_msedge()
        cmd = [
            edge_path,
            "--headless",
            "--no-pdf-header-footer",
            f"--print-to-pdf={dest_path}",
            temp_html
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        ctx.show_toast(ctx.i18n.t("success.pdf_exported"))
    except Exception as e:
        ctx.show_toast(f"{ctx.i18n.t('error.export_failed')}: {e}", duration=4000)
    finally:
        if os.path.exists(temp_html):
            os.remove(temp_html)
