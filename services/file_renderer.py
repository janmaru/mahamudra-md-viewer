from __future__ import annotations

import csv
import datetime
import html as html_module
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

import markdown

from constants import FONT_MONO
from services.css_loader import build_html
import services.mermaid_processor as mermaid_processor
import services.svg_processor as svg_processor
from services.diagram_cache import set_document as set_cache_document
from services.log_renderer import render_log

if TYPE_CHECKING:
    from app_context import AppContext

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg")
CODE_EXTS = (".py", ".js", ".ts", ".json", ".yaml", ".yml", ".txt")


class FileRenderer:
    def __init__(self, ctx: AppContext):
        self._ctx = ctx

    def open_file_dialog(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Markdown files", "*.md *.markdown *.mdown *.mkd"),
                       ("PDF files", "*.pdf"),
                       ("Log files", "*.log"),
                       ("Text files", "*.txt"),
                       ("Code files", "*.py *.js *.ts *.json *.yaml *.yml"),
                       ("CSV files", "*.csv"),
                       ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.svg"),
                       ("All files", "*.*")]
        )
        if path:
            self._ctx.load_file(Path(path))

    def load_file(self, path: Path, push_history: bool = True, fragment: str | None = None) -> None:
        ctx = self._ctx
        if push_history and ctx.current_file and ctx.current_file != path:
            ctx.history.append(ctx.current_file)
            ctx.show_toast(ctx.i18n.t("success.file_opened", name=path.name))

        ctx.root.title(f"{path.name} - Friedrich - Document Reader")
        if path not in ctx.recent_files:
            ctx.recent_files.insert(0, path)
            if len(ctx.recent_files) > 10:
                ctx.recent_files.pop()
            ctx.update_recent_list()

        ext = path.suffix.lower()

        if ext == ".pdf":
            tab = ctx.current_tab
            if tab and tab.pdf_viewer is not None:
                tab.pdf_viewer.load(path, zoom_percent=ctx.zoom_level)
            self._update_status(path, "")
            return

        if ext in IMAGE_EXTS:
            if ctx.view_mode == "preview":
                html_body = self._render_image(path)
                full_html = build_html(html_body, ctx.css_path, zoom=ctx.zoom_level)
                ctx.html_frame.load_html(full_html)
            else:
                ctx.source_text.delete("1.0", tk.END)
                try:
                    size = path.stat().st_size
                    ctx.source_text.insert("1.0", f"File: {path}\nSize: {size:,} bytes")
                except OSError:
                    ctx.source_text.insert("1.0", f"File: {path}")
            self._update_status(path, f"[Image: {path.name}]")
            return

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding="latin-1")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load file: {e}")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file: {e}")
            return

        if ctx.view_mode == "preview":
            if ext == ".log":
                dark_bg = "dark" in (ctx.css_path.stem if ctx.css_path else "dark")
                html_body = render_log(content, dark_bg=dark_bg)
            elif ext == ".csv":
                html_body = self._render_csv(content)
            elif ext in CODE_EXTS:
                html_body = self._render_code(content, ext)
            else:
                set_cache_document(path)
                html_body = self._render_markdown(content, async_mermaid=True)
                full_html = build_html(html_body, ctx.css_path, zoom=ctx.zoom_level)
                base_url_uri = path.parent.as_uri() + "/"
                ctx.last_fragment = fragment
                ctx.html_frame.load_html(full_html, base_url=base_url_uri, fragment=fragment)
                self._render_diagrams_async(content)
                self._update_status(path, content)
                return

            full_html = build_html(html_body, ctx.css_path, zoom=ctx.zoom_level)
            base_url_uri = path.parent.as_uri() + "/"
            ctx.html_frame.load_html(full_html, base_url=base_url_uri, fragment=fragment)
        else:
            ctx.source_text.delete("1.0", tk.END)
            ctx.source_text.insert("1.0", content)

        self._update_status(path, content)

    def update_html(self, html_body: str) -> None:
        ctx = self._ctx
        ctx.last_html_body = html_body
        if ctx.html_frame is None:
            return
        if ctx.current_file and ctx.view_mode == "preview":
            full_html = build_html(html_body, ctx.css_path, zoom=ctx.zoom_level)
            base_url_uri = ctx.current_file.parent.as_uri() + "/"
            fragment = getattr(ctx, "last_fragment", None)
            ctx.html_frame.load_html(full_html, base_url=base_url_uri, fragment=fragment)

    def apply_zoom(self) -> None:
        ctx = self._ctx
        ctx.show_toast(ctx.i18n.t("toast.zoom_level", level=ctx.zoom_level), duration=800)
        tab = ctx.current_tab
        if tab and tab.pdf_viewer is not None:
            tab.pdf_viewer.set_zoom(ctx.zoom_level)
            return
        if ctx.last_html_body:
            self.update_html(ctx.last_html_body)
        scale = ctx.zoom_level / 100.0
        new_size = max(8, int(11 * scale))
        if ctx.source_text is not None:
            ctx.source_text.configure(font=(FONT_MONO, new_size))

    def _render_markdown(self, content: str, async_mermaid: bool = True) -> str:
        ctx = self._ctx
        ctx.diagram_registry.clear()

        processed_content, mermaid_blocks = mermaid_processor.process_mermaid_blocks(content)
        processed_content, svg_blocks = svg_processor.process_svg_blocks(processed_content)

        html_body = markdown.markdown(processed_content, extensions=["tables", "fenced_code", "sane_lists"])

        if mermaid_blocks and async_mermaid:
            html_body = mermaid_processor.inject_mermaid_placeholders(html_body, mermaid_blocks)
        elif mermaid_blocks:
            html_body = mermaid_processor.inject_mermaid_svgs(
                html_body, mermaid_blocks, ctx.diagram_registry)

        if svg_blocks and async_mermaid:
            html_body = svg_processor.inject_svg_placeholders(html_body, svg_blocks)
        elif svg_blocks:
            html_body = svg_processor.inject_svg_images(
                html_body, svg_blocks, ctx.diagram_registry)

        html_body = html_body.replace("<table>", '<div class="table-container"><table>')
        html_body = html_body.replace("</table>", "</table></div>")

        ctx.last_html_body = html_body
        return html_body

    def _render_diagrams_async(self, content: str) -> None:
        ctx = self._ctx
        registry = {}
        ctx.diagram_render_in_flight += 1

        def _worker():
            try:
                processed_content, mermaid_blocks = mermaid_processor.process_mermaid_blocks(content)
                processed_content, svg_blocks = svg_processor.process_svg_blocks(processed_content)
                if not mermaid_blocks and not svg_blocks:
                    return
                html_body = markdown.markdown(processed_content, extensions=["tables", "fenced_code", "sane_lists"])
                if mermaid_blocks:
                    html_body = mermaid_processor.inject_mermaid_svgs(
                        html_body, mermaid_blocks, registry)
                if svg_blocks:
                    html_body = svg_processor.inject_svg_images(
                        html_body, svg_blocks, registry)
                html_body = html_body.replace("<table>", '<div class="table-container"><table>')
                html_body = html_body.replace("</table>", "</table></div>")
                ctx.root.after(0, lambda: self._on_diagrams_ready(html_body, registry))
            finally:
                ctx.root.after(0, self._on_diagrams_done)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_diagrams_ready(self, html_body: str, registry: dict) -> None:
        self._ctx.diagram_registry.update(registry)
        self.update_html(html_body)

    def _on_diagrams_done(self) -> None:
        if self._ctx.diagram_render_in_flight > 0:
            self._ctx.diagram_render_in_flight -= 1

    def _render_csv(self, content: str) -> str:
        reader = csv.reader(content.splitlines())
        rows = list(reader)
        if not rows:
            return "<p>Empty CSV</p>"
        html = '<div class="table-container"><table><thead><tr>'
        html += "".join(f"<th>{html_module.escape(cell)}</th>" for cell in rows[0])
        html += "</tr></thead><tbody>"
        for row in rows[1:]:
            html += "<tr>" + "".join(f"<td>{html_module.escape(cell)}</td>" for cell in row) + "</tr>"
        html += "</tbody></table></div>"
        return html

    def _render_code(self, content: str, ext: str) -> str:
        lang = {".py": "python", ".js": "javascript", ".ts": "typescript",
                ".json": "json", ".yaml": "yaml", ".yml": "yaml"}.get(ext, "")
        escaped = html_module.escape(content)
        return (f'<pre style="padding:20px;overflow-x:auto;line-height:1.5;">'
                f'<code class="language-{lang}">{escaped}</code></pre>')

    def _render_image(self, path: Path) -> str:
        uri = path.as_uri()
        return f'<div style="text-align:center;padding:20px;"><img src="{uri}" style="max-width:100%;max-height:90vh;"></div>'

    def _update_status(self, path: Path, content: str) -> None:
        try:
            mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            mtime = "unknown"
        lines = len(content.splitlines())
        
        i18n = self._ctx.i18n
        status_text = f"  {path.name}    {i18n.t('status.lines', count=lines)}    {i18n.t('status.modified', time=mtime)}    UTF-8"
        self._ctx.root.status_label.config(text=status_text)
