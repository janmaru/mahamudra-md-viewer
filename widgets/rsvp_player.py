from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Sequence

from services.rd_parser import InlineSpan, Sentence

_MIN_SENTENCE_MS = 800
_DEFAULT_WPM = 300
_MIN_WPM = 200
_MAX_WPM = 1200


class RsvpPlayer(ttk.Frame):
    """Tkinter widget that plays a sequence of `Sentence` objects RSVP-style.

    One sentence at a time fills the central area. Per-sentence duration is
    derived from the configured WPM: `max(_MIN_SENTENCE_MS, words / wpm * 60_000)`.
    """

    def __init__(self, master: tk.Misc, *, wpm: int = _DEFAULT_WPM) -> None:
        super().__init__(master)
        self._sentences: list[Sentence] = []
        self._index = 0
        self._playing = False
        self._after_id: str | None = None
        self._wpm_var = tk.IntVar(value=wpm)
        self._progress_var = tk.StringVar(value="0 / 0")
        self._wpm_label_var = tk.StringVar(value=f"{wpm} WPM")

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._text = tk.Text(
            self,
            wrap="word",
            font=("Segoe UI", 28),
            relief="flat",
            padx=40,
            pady=40,
            height=6,
            state="disabled",
            cursor="arrow",
        )
        self._text.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self._text.tag_configure("normal", justify="center")
        self._text.tag_configure("bold", font=("Segoe UI", 28, "bold"), justify="center")
        self._text.tag_configure("italic", font=("Segoe UI", 28, "italic"), justify="center")
        self._text.tag_configure(
            "code",
            font=("Consolas", 26),
            background="#2d2d30",
            foreground="#d7ba7d",
            justify="center",
        )

        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        for i in range(7):
            controls.columnconfigure(i, weight=0)
        controls.columnconfigure(5, weight=1)

        self._prev_btn = ttk.Button(controls, text="⏮", width=3, command=self.prev)
        self._prev_btn.grid(row=0, column=0, padx=2)

        self._play_btn = ttk.Button(controls, text="▶", width=3, command=self.toggle)
        self._play_btn.grid(row=0, column=1, padx=2)

        self._next_btn = ttk.Button(controls, text="⏭", width=3, command=self.next)
        self._next_btn.grid(row=0, column=2, padx=2)

        self._stop_btn = ttk.Button(controls, text="⏹", width=3, command=self.stop)
        self._stop_btn.grid(row=0, column=3, padx=(2, 12))

        ttk.Label(controls, textvariable=self._progress_var).grid(row=0, column=4, padx=8)

        self._wpm_scale = ttk.Scale(
            controls,
            from_=_MIN_WPM,
            to=_MAX_WPM,
            orient="horizontal",
            variable=self._wpm_var,
            command=self._on_wpm_change,
        )
        self._wpm_scale.grid(row=0, column=5, sticky="ew", padx=8)

        ttk.Label(controls, textvariable=self._wpm_label_var, width=10).grid(row=0, column=6)

    def load(self, sentences: Sequence[Sentence]) -> None:
        self.stop()
        self._sentences = list(sentences)
        self._index = 0
        self._render_current()

    def toggle(self) -> None:
        if not self._sentences:
            return
        if self._playing:
            self._pause()
        else:
            self._play()

    def stop(self) -> None:
        self._cancel_timer()
        self._playing = False
        self._index = 0
        self._play_btn.configure(text="▶")
        self._render_current()

    def next(self) -> None:
        if not self._sentences:
            return
        was_playing = self._playing
        self._cancel_timer()
        if self._index < len(self._sentences) - 1:
            self._index += 1
            self._render_current()
            if was_playing:
                self._schedule_next()
        else:
            self._pause()

    def prev(self) -> None:
        if not self._sentences:
            return
        was_playing = self._playing
        self._cancel_timer()
        if self._index > 0:
            self._index -= 1
        self._render_current()
        if was_playing:
            self._schedule_next()

    def _play(self) -> None:
        if not self._sentences:
            return
        self._playing = True
        self._play_btn.configure(text="⏸")
        self._schedule_next()

    def _pause(self) -> None:
        self._cancel_timer()
        self._playing = False
        self._play_btn.configure(text="▶")

    def _schedule_next(self) -> None:
        self._cancel_timer()
        if not self._playing or not self._sentences:
            return
        duration_ms = self._duration_for(self._sentences[self._index])
        self._after_id = self.after(duration_ms, self._advance)

    def _advance(self) -> None:
        self._after_id = None
        if self._index < len(self._sentences) - 1:
            self._index += 1
            self._render_current()
            self._schedule_next()
        else:
            self._pause()

    def _cancel_timer(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _duration_for(self, sentence: Sentence) -> int:
        wpm = max(1, self._wpm_var.get())
        words = max(1, sentence.word_count)
        ms = int(words / wpm * 60_000)
        return max(_MIN_SENTENCE_MS, ms)

    def _on_wpm_change(self, _value: str) -> None:
        wpm = self._wpm_var.get()
        self._wpm_label_var.set(f"{wpm} WPM")
        if self._playing:
            self._schedule_next()

    def _render_current(self) -> None:
        total = len(self._sentences)
        if total == 0:
            self._set_text(())
            self._progress_var.set("0 / 0")
            return
        sentence = self._sentences[self._index]
        self._set_text(sentence.spans)
        self._progress_var.set(f"{self._index + 1} / {total}")

    def _set_text(self, spans: Sequence[InlineSpan]) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        for span in spans:
            tag = self._tag_for(span)
            self._text.insert("end", span.text, (tag,))
        self._text.configure(state="disabled")

    @staticmethod
    def _tag_for(span: InlineSpan) -> str:
        if span.code:
            return "code"
        if span.bold:
            return "bold"
        if span.italic:
            return "italic"
        return "normal"
