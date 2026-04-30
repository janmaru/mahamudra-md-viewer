from __future__ import annotations

import base64
import tkinter as tk
from tkinter import filedialog, messagebox

from constants import FONT
from i18n import get_i18n


class DiagramViewer(tk.Toplevel):
    """Zoomable diagram viewer window with mouse wheel zoom and drag pan."""

    def __init__(self, master, png_b64: str, colors: dict):
        super().__init__(master)
        self.title("Diagram Viewer")
        self.colors = colors
        self.configure(bg=self.colors["bg"])
        self.geometry("900x700")

        self._zoom = 1.0
        self._pan_start = None

        import io
        from PIL import Image, ImageTk
        raw = base64.b64decode(png_b64)
        self._pil_image = Image.open(io.BytesIO(raw))

        toolbar = tk.Frame(self, bg=self.colors["toolbar"], height=32)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.pack_propagate(False)

        t = get_i18n().t
        for text, cmd in [("Zoom +", self._zoom_in), ("Zoom -", self._zoom_out),
                          ("Fit", self._fit), ("1:1", self._reset_zoom),
                          (t("btn.save_image"), self._save_image)]:
            btn = tk.Label(toolbar, text=text, bg=self.colors["toolbar"], fg=self.colors["secondary"],
                           font=(FONT, 10), padx=10, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors["btn_hover"], fg=self.colors["text_bright"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors["toolbar"], fg=self.colors["secondary"]))

        self._zoom_label = tk.Label(toolbar, text="100%", bg=self.colors["toolbar"],
                                    fg=self.colors["text"], font=(FONT, 10))
        self._zoom_label.pack(side=tk.RIGHT, padx=10)

        self._canvas = tk.Canvas(self, bg=self.colors["bg"], highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True)

        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self._canvas.bind("<B1-Motion>", self._on_pan_move)

        self._tk_image = None
        self.after(50, self._fit)

    def _render(self):
        w = max(1, int(self._pil_image.width * self._zoom))
        h = max(1, int(self._pil_image.height * self._zoom))
        from PIL import Image, ImageTk
        resized = self._pil_image.resize((w, h), Image.LANCZOS)
        self._tk_image = ImageTk.PhotoImage(resized)
        self._canvas.delete("all")
        self._canvas.create_image(self._canvas.winfo_width() // 2,
                                  self._canvas.winfo_height() // 2,
                                  image=self._tk_image, anchor=tk.CENTER)
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._zoom_label.config(text=f"{int(self._zoom * 100)}%")

    def _zoom_in(self):
        self._zoom = min(self._zoom * 1.25, 10.0)
        self._render()

    def _zoom_out(self):
        self._zoom = max(self._zoom / 1.25, 0.1)
        self._render()

    def _fit(self):
        self.update_idletasks()
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        zw = cw / self._pil_image.width
        zh = ch / self._pil_image.height
        self._zoom = min(zw, zh, 1.0)
        self._render()

    def _reset_zoom(self):
        self._zoom = 1.0
        self._render()

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _on_pan_start(self, event):
        self._pan_start = (event.x, event.y)
        self._canvas.scan_mark(event.x, event.y)

    def _on_pan_move(self, event):
        self._canvas.scan_dragto(event.x, event.y, gain=1)

    def _save_image(self):
        from pathlib import Path
        t = get_i18n().t
        dest = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile="diagram.png",
            title=t("dialog.save_as"),
        )
        if not dest:
            return
        dest_path = Path(dest)
        if dest_path.suffix.lower() != ".png":
            dest_path = dest_path.with_suffix(".png")
        try:
            self._pil_image.save(dest_path, format="PNG")
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                t("dialog.error"),
                t("error.save_image_failed", error=str(exc)),
                parent=self,
            )
