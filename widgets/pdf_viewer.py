from __future__ import annotations

import traceback
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app_context import AppContext
    from PIL import ImageTk


PAGE_GAP = 8
BASE_DPI = 96
PDF_DPI = 72
MAX_PAGES = 50  # cap to keep memory bounded on huge PDFs


class PdfViewer(tk.Frame):
    """Continuous-scroll PDF viewer backed by pypdfium2."""

    def __init__(self, master: tk.Misc, ctx: "AppContext") -> None:
        super().__init__(master, bg=ctx.colors["bg"])
        self._ctx = ctx
        self._path: Optional[Path] = None
        self._zoom: int = 100
        self._pdf = None
        self._photo_images: list["ImageTk.PhotoImage"] = []
        self._page_items: list[int] = []
        self._render_pending: bool = False

        self._canvas = tk.Canvas(
            self, bg=ctx.colors["bg"], highlightthickness=0, takefocus=1
        )
        self._scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind("<Destroy>", self._on_destroy)

    def load(self, path: Path, zoom_percent: int = 100) -> None:
        self._path = path
        self._zoom = zoom_percent
        self._open_pdf()
        self._schedule_render()

    def set_zoom(self, percent: int) -> None:
        if percent == self._zoom or self._pdf is None:
            return
        self._zoom = percent
        scroll_pos = self._canvas.yview()[0]
        self._schedule_render()
        self._canvas.yview_moveto(scroll_pos)

    def _open_pdf(self) -> None:
        import pypdfium2 as pdfium
        self._close_pdf()
        self._pdf = pdfium.PdfDocument(str(self._path))

    def _close_pdf(self) -> None:
        if self._pdf is None:
            return
        try:
            self._pdf.close()
        except Exception:
            traceback.print_exc()
        finally:
            self._pdf = None

    def _schedule_render(self) -> None:
        # Coalesce concurrent triggers (zoom, <Configure>, deferred re-render)
        # so only one _render runs per idle cycle. Without this, page lists
        # can be cleared by one render while another is iterating them.
        if self._render_pending:
            return
        self._render_pending = True
        self.after_idle(self._render)

    def _render(self) -> None:
        self._render_pending = False
        if self._pdf is None:
            return
        canvas = self._canvas
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        if canvas_width < 10:
            self.after(50, self._schedule_render)
            return

        from PIL import ImageTk

        canvas.delete("all")
        self._photo_images.clear()
        self._page_items.clear()

        scale = (self._zoom / 100.0) * (BASE_DPI / PDF_DPI)
        y = PAGE_GAP
        max_w = 0

        total_pages = len(self._pdf)
        page_count = min(total_pages, MAX_PAGES)
        if total_pages > MAX_PAGES:
            self._ctx.show_toast(
                self._ctx.i18n.t("toast.pdf_truncated", count=MAX_PAGES),
                duration=4000,
            )

        for i in range(page_count):
            try:
                page = self._pdf[i]
                try:
                    bitmap = page.render(scale=scale)
                    pil = bitmap.to_pil()
                finally:
                    page.close()
            except Exception:
                traceback.print_exc()
                continue
            photo = ImageTk.PhotoImage(pil)
            self._photo_images.append(photo)
            x = max((canvas_width - pil.width) // 2, 0)
            item = canvas.create_image(x, y, image=photo, anchor=tk.NW)
            self._page_items.append(item)
            y += pil.height + PAGE_GAP
            max_w = max(max_w, pil.width)

        canvas.configure(scrollregion=(0, 0, max(max_w, canvas_width), y))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        if not self._page_items:
            return
        canvas_width = event.width
        for item, photo in zip(self._page_items, self._photo_images):
            current = self._canvas.coords(item)
            if not current:
                continue
            new_x = max((canvas_width - photo.width()) // 2, 0)
            if new_x != current[0]:
                self._canvas.coords(item, new_x, current[1])

    def _on_mousewheel(self, event: tk.Event) -> None:
        # Linux delivers delta as +/-1 directly; Windows/macOS use multiples of 120.
        delta = event.delta
        if abs(delta) >= 120:
            step = int(-delta / 120) * 3
        else:
            step = -delta * 3
        if step:
            self._canvas.yview_scroll(step, "units")

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self:
            self._close_pdf()
            self._photo_images.clear()
            self._page_items.clear()
