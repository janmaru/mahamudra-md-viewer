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
from services.diagram_cache import set_document as set_cache_document, current_document as cache_document
from services.log_renderer import render_log

if TYPE_CHECKING:
    from app_context import AppContext

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg")
CODE_EXTS = (".py", ".js", ".ts", ".json", ".yaml", ".yml", ".txt")
MARKDOWN_EXTS = (".md", ".markdown", ".mdown", ".mkd")


class FileRenderer:
    def __init__(self, ctx: AppContext):
        self._ctx = ctx
        # Generation stamp for async diagram workers: only the latest render's
        # result may touch the HTML frame (live preview fires many in a row).
        self._render_seq = 0

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
        # "split" shows the editor and the preview side by side, so both
        # branches below run; "preview" / "source" run exactly one of them.
        show_html = ctx.view_mode in ("preview", "split")
        show_source = ctx.view_mode in ("source", "split")

        if ext == ".pdf":
            tab = ctx.current_tab
            if tab and tab.pdf_viewer is not None:
                tab.pdf_viewer.load(path, zoom_percent=ctx.zoom_level)
            self._update_status(path, "")
            return

        if ext in IMAGE_EXTS:
            if show_source and self._may_replace_buffer():
                try:
                    size = path.stat().st_size
                    meta = f"File: {path}\nSize: {size:,} bytes"
                except OSError:
                    meta = f"File: {path}"
                if ctx.current_tab is not None:
                    ctx.current_tab.set_source(meta)
                self._mark_source_clean()
            if show_html:
                ctx.last_fragment = None
                html_body = self._render_image(path)
                self._remember_body(html_body)
                full_html = build_html(html_body, ctx.css_path, zoom=ctx.zoom_level)
                ctx.html_frame.load_html(full_html)
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

        if show_source and self._may_replace_buffer():
            if ctx.current_tab is not None:
                ctx.current_tab.set_source(content)
            self._mark_source_clean()

        if show_html:
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
                ctx.html_frame.load_html(full_html, base_url=base_url_uri, fragment=fragment)
                # The anchor survives only until the pending diagram swap
                # re-applies it; with no worker there is nothing to re-apply.
                ctx.last_fragment = fragment if self._render_diagrams_async(content) else None
                self._update_status(path, content)
                return

            self._remember_body(html_body)
            full_html = build_html(html_body, ctx.css_path, zoom=ctx.zoom_level)
            base_url_uri = path.parent.as_uri() + "/"
            ctx.last_fragment = None
            ctx.html_frame.load_html(full_html, base_url=base_url_uri, fragment=fragment)

        self._update_status(path, content)

    def _remember_body(self, html_body: str) -> None:
        """Record the rendered body on the active tab (and mirror it on the
        context). Zoom repaints from the tab's own copy, so switching tabs can
        never paint one document into another's frame."""
        ctx = self._ctx
        ctx.last_html_body = html_body
        if ctx.current_tab is not None:
            ctx.current_tab.last_html_body = html_body

    def _may_replace_buffer(self) -> bool:
        """False when the editor holds unsaved work: a disk load must never
        overwrite it (and ``set_source`` clears undo, so it would be
        unrecoverable). Callers that legitimately reload a clean tab are
        unaffected."""
        tab = self._ctx.current_tab
        return tab is None or not (tab.is_dirty or tab.is_untitled)

    def _mark_source_clean(self) -> None:
        """Reset the source widget's modified flag and the active tab's dirty
        state after a programmatic load — typing-driven edits should be the
        only thing that flips the dirty marker."""
        ctx = self._ctx
        if ctx.source_text is None:
            return
        ctx.source_text.edit_reset()  # a disk load is not an undoable edit
        ctx.source_text.edit_modified(False)
        tab = ctx.current_tab
        if tab is not None:
            tab.is_dirty = False

    def render_in_memory(self, content: str, base_path: Path | None = None,
                         fragment: str | None = None) -> None:
        """Render markdown from an in-memory string into the current tab's HTML frame.

        Used when the source view is dirty or the tab is untitled: the disk
        copy is stale or absent, so we render what the editor currently holds.
        """
        ctx = self._ctx
        if ctx.html_frame is None:
            return
        tab = ctx.current_tab
        if base_path is not None and base_path.exists():
            set_cache_document(base_path)
        elif tab is not None:
            set_cache_document(tab.path)  # untitled: stable per-tab key ("untitled-N")
        html_body = self._render_markdown(content, async_mermaid=True)
        full_html = build_html(html_body, ctx.css_path, zoom=ctx.zoom_level)
        base_dir = (base_path.parent if base_path is not None else ctx.scan_dir)
        base_url_uri = base_dir.as_uri() + "/"
        self._load_html_keep_scroll(ctx.html_frame, full_html, base_url_uri, fragment)
        ctx.last_fragment = fragment if self._render_diagrams_async(content) else None
        self._update_status_string(base_path, content)

    @staticmethod
    def _load_html_keep_scroll(frame, full_html: str, base_url: str, fragment: str | None) -> None:
        """Reload ``frame`` with ``full_html`` and restore the previous vertical
        scroll fraction. Used by live preview and by the async diagram swap so
        the reader does not jump back to the top on every re-render. A
        fragment always wins over the remembered position."""
        try:
            # HtmlFrame.yview() forwards without returning; ask the inner widget.
            y = float(frame.html.yview()[0])
        except (AttributeError, TypeError, IndexError, tk.TclError):
            y = 0.0
        frame.load_html(full_html, base_url=base_url, fragment=fragment)
        if fragment or y <= 0.0:
            return

        def _restore():
            try:
                frame.yview_moveto(y)
            except tk.TclError:
                pass
        frame.after(50, _restore)

    def _update_status_string(self, path: Path | None, content: str) -> None:
        if path is not None and path.exists():
            self._update_status(path, content)  # same fields as a disk load (incl. mtime)
            return
        name = path.name if path is not None else "untitled.md"
        lines = len(content.splitlines())
        i18n = self._ctx.i18n
        status_text = f"  {name}    {i18n.t('status.lines', count=lines)}    UTF-8"
        self._ctx.root.status_label.config(text=status_text)

    def update_html(self, html_body: str) -> None:
        ctx = self._ctx
        self._remember_body(html_body)
        if ctx.html_frame is None:
            return
        tab = ctx.current_tab
        if tab is None or ctx.view_mode not in ("preview", "split"):
            return
        # Untitled tabs carry a relative virtual path: resolve links against
        # the scan directory instead (Path(".").as_uri() raises ValueError).
        base_dir = ctx.scan_dir if tab.is_untitled else tab.path.parent
        full_html = build_html(html_body, ctx.css_path, zoom=ctx.zoom_level)
        # The anchor is re-applied once (the diagram swap changes the document
        # height); leaving it set would disable scroll preservation for good.
        fragment = ctx.last_fragment
        ctx.last_fragment = None
        self._load_html_keep_scroll(ctx.html_frame, full_html, base_dir.as_uri() + "/", fragment)

    def apply_zoom(self, quiet: bool = False) -> None:
        ctx = self._ctx
        if not quiet:
            ctx.show_toast(ctx.i18n.t("toast.zoom_level", level=ctx.zoom_level), duration=800)
        tab = ctx.current_tab
        if tab and tab.pdf_viewer is not None:
            tab.pdf_viewer.set_zoom(ctx.zoom_level)
            return
        if tab is not None and tab.last_html_body:
            self.update_html(tab.last_html_body)
        scale = ctx.zoom_level / 100.0
        new_size = max(8, int(11 * scale))
        if ctx.source_text is not None:
            ctx.source_text.configure(font=(FONT_MONO, new_size))
        if tab and tab.highlighter is not None:
            tab.highlighter.set_font_size(new_size)
        if tab and tab.line_numbers is not None:
            tab.line_numbers.set_font_size(new_size)

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

        self._remember_body(html_body)
        return html_body

    def _render_diagrams_async(self, content: str) -> bool:
        """Spawn the diagram worker. Returns False when the document has no
        diagram block, so callers know no later swap will repaint the page."""
        ctx = self._ctx
        processed_content, mermaid_blocks = mermaid_processor.process_mermaid_blocks(content)
        processed_content, svg_blocks = svg_processor.process_svg_blocks(processed_content)
        if not mermaid_blocks and not svg_blocks:
            return False  # nothing to render: no worker, no in-flight gate
        self._render_seq += 1
        seq = self._render_seq
        owner = ctx.current_tab  # the worker's HTML belongs to this tab only
        doc_key = cache_document()  # snapshot now: the global may move to another tab
        registry = {}
        ctx.diagram_render_in_flight += 1

        def _worker():
            try:
                html_body = markdown.markdown(processed_content, extensions=["tables", "fenced_code", "sane_lists"])
                if mermaid_blocks:
                    html_body = mermaid_processor.inject_mermaid_svgs(
                        html_body, mermaid_blocks, registry, doc=doc_key)
                if svg_blocks:
                    html_body = svg_processor.inject_svg_images(
                        html_body, svg_blocks, registry, doc=doc_key)
                html_body = html_body.replace("<table>", '<div class="table-container"><table>')
                html_body = html_body.replace("</table>", "</table></div>")
                ctx.root.after(0, lambda: self._on_diagrams_ready(html_body, registry, seq, owner))
            finally:
                ctx.root.after(0, self._on_diagrams_done)

        threading.Thread(target=_worker, daemon=True).start()
        return True

    def _on_diagrams_ready(self, html_body: str, registry: dict, seq: int, owner) -> None:
        current = self._ctx.current_tab
        if seq != self._render_seq or owner is not current:
            # Superseded by a newer render, or the user switched tabs: never
            # paint this HTML (its "dN" registry keys are obsolete too). A clean
            # tab left behind keeps its placeholders, so make it re-render when
            # reselected; dirty / untitled tabs re-render on the next edit.
            if owner is not None and owner is not current and not (owner.is_dirty or owner.is_untitled):
                owner.rendered = False
            return
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
