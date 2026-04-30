from __future__ import annotations

import tkinter as tk
import webbrowser
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from constants import FONT, get_version
from widgets.custom_menu import CustomMenu

if TYPE_CHECKING:
    from app_context import AppContext


@dataclass
class ToolbarCommands:
    open_file: Callable
    change_folder: Callable
    export_pdf: Callable
    toggle_sidebar: Callable
    toggle_zen: Callable
    toggle_view: Callable
    go_back: Callable
    toggle_ui_theme: Callable
    refresh_all: Callable
    copy_content: Callable
    clear_diagram_cache: Callable
    zoom_in: Callable
    zoom_out: Callable
    reset_zoom: Callable
    toggle_status_bar: Callable
    set_markdown_theme: Callable
    quit: Callable


class Toolbar:
    def __init__(self, parent: tk.Tk, ctx: AppContext, commands: ToolbarCommands):
        self._parent = parent
        self._ctx = ctx
        self._cmd = commands
        colors = ctx.colors

        # Titlebar
        self.titlebar = tk.Frame(parent, bg=colors["titlebar"], height=2)
        self.titlebar.pack(side=tk.TOP, fill=tk.X)

        # Toolbar
        self.frame = tk.Frame(parent, bg=colors["toolbar"], bd=0, height=34)
        self.frame.pack(side=tk.TOP, fill=tk.X)
        self.separator = tk.Frame(parent, bg=colors["border"], height=1)
        self.separator.pack(side=tk.TOP, fill=tk.X)

        # LEFT: Menu Bar
        i18n = self._ctx.i18n
        self._menu_buttons = {}
        self._menu_buttons["file"] = self._make_menubar_btn(self.frame, i18n.t("menu.file"), self._show_file_menu)
        self._menu_buttons["view"] = self._make_menubar_btn(self.frame, i18n.t("menu.view"), self._show_view_menu)
        self._menu_buttons["tools"] = self._make_menubar_btn(self.frame, i18n.t("menu.tools"), self._show_tools_menu)

    def set_menu_enabled(self, name: str, enabled: bool):
        btn = self._menu_buttons.get(name)
        if not btn: return
        colors = self._ctx.colors
        if enabled:
            btn.config(fg=colors["text"], cursor="hand2")
            # Re-bind logic is handled by _make_menubar_btn bindings if we don't unbind them
        else:
            btn.config(fg=colors["border"], cursor="")

    def _make_menubar_btn(self, parent, text, command):
        colors = self._ctx.colors
        btn = tk.Label(parent, text=text, bg=colors["toolbar"], fg=colors["text"],
                       font=(FONT, 10), padx=12, pady=4, cursor="hand2")
        btn.pack(side=tk.LEFT)
        btn.bind("<Button-1>", lambda e: command(e))
        btn.bind("<Enter>", lambda e: btn.config(bg=colors["btn_hover"], fg=colors["text_bright"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=colors["toolbar"], fg=colors["text"]))
        return btn

    def _make_icon_btn(self, parent, text, command, side=tk.RIGHT):
        colors = self._ctx.colors
        btn = tk.Label(parent, text=text, bg=colors["toolbar"], fg=colors["secondary"],
                       font=(FONT, 10), padx=10, pady=4, cursor="hand2")
        btn.pack(side=side)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg=colors["btn_hover"], fg=colors["text_bright"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=colors["toolbar"], fg=colors["secondary"]))
        return btn

    def _vsep_right(self, parent):
        tk.Frame(parent, bg=self._ctx.colors["border"], width=1).pack(side=tk.RIGHT, fill=tk.Y, pady=6)

    def _popup_menu(self, event, items):
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty() + event.widget.winfo_height()
        CustomMenu(self._parent, items, self._ctx.colors).geometry(f"+{x}+{y}")

    def _show_file_menu(self, event):
        i18n = self._ctx.i18n
        items = [
            (f"{i18n.t('menu.open_file')}      Ctrl+O", self._cmd.open_file),
            (i18n.t('menu.open_folder'), self._cmd.change_folder),
            ("---", None),
            (i18n.t('menu.export_pdf'), self._cmd.export_pdf),
            ("---", None),
            (i18n.t('menu.exit'), self._cmd.quit)
        ]
        self._popup_menu(event, items)

    def _show_view_menu(self, event):
        cmd = self._cmd
        i18n = self._ctx.i18n
        items = [
            (f"{i18n.t('menu.toggle_sidebar')}    Ctrl+B", cmd.toggle_sidebar),
            (i18n.t('menu.toggle_status_bar'), cmd.toggle_status_bar),
            (f"{i18n.t('menu.toggle_zen')}   F11", cmd.toggle_zen),
            ("---", None),
            (f"{i18n.t('menu.zoom_in')}           Ctrl++", cmd.zoom_in),
            (f"{i18n.t('menu.zoom_out')}          Ctrl+-", cmd.zoom_out),
            (f"{i18n.t('menu.reset_zoom')}        Ctrl+0", cmd.reset_zoom),
            ("---", None),
            (f"{i18n.t('menu.toggle_ui_theme')}   (Light/Dark)", cmd.toggle_ui_theme),
            ("---", None)
        ]
        for name in self._ctx.theme_names:
            items.append((f"MD: {name}", lambda n=name: cmd.set_markdown_theme(n)))
        self._popup_menu(event, items)

    def _show_tools_menu(self, event):
        i18n = self._ctx.i18n
        items = [
            (f"{i18n.t('menu.refresh')}       Ctrl+R", self._cmd.refresh_all),
            (f"{i18n.t('menu.copy_content')}     Ctrl+C", self._cmd.copy_content),
            ("---", None),
            (i18n.t('menu.clear_cache'), self._cmd.clear_diagram_cache),
            ("---", None),
            (i18n.t('menu.about'), self.show_about)
        ]
        self._popup_menu(event, items)

    def show_about(self):
        colors = self._ctx.colors
        i18n = self._ctx.i18n
        about = tk.Toplevel(self._parent)
        about.title(i18n.t("dialog.about"))
        about.geometry("420x420")
        about.configure(bg=colors["bg"])
        about.resizable(False, False)
        about.transient(self._parent)
        about.grab_set()

        header = tk.Frame(about, bg="#88398a", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        icon_label = tk.Label(header, bg="#88398a")
        try:
            from PIL import Image, ImageTk
            from constants import APP_DIR
            icon_path = APP_DIR / "app_icon.ico"
            if icon_path.exists():
                pil_icon = Image.open(icon_path)
                pil_icon.load()
                pil_icon = pil_icon.convert("RGBA").resize((56, 56), Image.LANCZOS)
                # Keep a reference on the Toplevel to prevent GC of the PhotoImage
                about._about_icon = ImageTk.PhotoImage(pil_icon)
                icon_label.configure(image=about._about_icon)
            else:
                icon_label.configure(text="M\u2193", fg="#ffffff", font=(FONT, 28, "bold"))
        except Exception:
            icon_label.configure(text="M\u2193", fg="#ffffff", font=(FONT, 28, "bold"))
        icon_label.pack(pady=10)

        content = tk.Frame(about, bg=colors["bg"], padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(content, text=i18n.t("app.title"), bg=colors["bg"], fg=colors["text_bright"],
                 font=(FONT, 14, "bold")).pack()
        tk.Label(content, text=i18n.t("app.version", version=get_version()), bg=colors["bg"], fg=colors["secondary"],
                 font=(FONT, 9)).pack(pady=(0, 15))

        desc = i18n.t("dialog.description")
        tk.Label(content, text=desc, bg=colors["bg"], fg=colors["text"],
                 font=(FONT, 10), wraplength=360, justify=tk.CENTER).pack()

        tk.Frame(content, bg=colors["border"], height=1).pack(fill=tk.X, pady=15)

        author_link = "https://janmaru.github.io"
        tk.Label(content, text=f"{i18n.t('dialog.author')}: janmaru", bg=colors["bg"], fg=colors["text_bright"],
                 font=(FONT, 10, "bold")).pack()

        lbl_link = tk.Label(content, text=author_link, bg=colors["bg"], fg=colors["link"],
                            font=(FONT, 9), cursor="hand2")
        lbl_link.pack()
        lbl_link.bind("<Button-1>", lambda e: webbrowser.open(author_link))

        footer = tk.Frame(about, bg=colors["bg"], pady=10)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        btn = tk.Label(footer, text=i18n.t("btn.close"), bg=colors["accent"], fg="#ffffff",
                       font=(FONT, 10, "bold"), padx=30, pady=8, cursor="hand2")
        btn.pack()
        btn.bind("<Button-1>", lambda e: about.destroy())
