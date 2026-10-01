"""Small custom widgets drawn on canvases."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from ui.theme import COLORS, font


def rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius, **options):
    r = radius
    points = [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
              x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
              x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r,
              x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **options)


class RoundedButton(tk.Canvas):
    """Flat rounded button with hover feedback."""

    STYLES = {
        "primary": ("accent", "accent_hover", "on_accent"),
        "secondary": ("card_alt", "border", "text"),
        "danger": ("danger_dim", "danger", "text"),
        "ghost": ("panel", "card_alt", "text"),
    }

    def __init__(self, master, text: str, command: Callable[[], None], width=210,
                 height=38, kind="secondary", parent_bg=None, size=10):
        super().__init__(master, width=width, height=height, highlightthickness=0,
                         bd=0, cursor="hand2", bg=parent_bg or COLORS["sidebar"])
        self._bw, self._bh = width, height
        self._text, self._command, self._size = text, command, size
        bg, hover, fg = self.STYLES[kind]
        self._bg, self._hover_bg, self._fg = COLORS[bg], COLORS[hover], COLORS[fg]
        self._hover = False
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", self._on_release)
        self._draw()

    def set_text(self, text: str) -> None:
        self._text = text
        self._draw()

    def _set_hover(self, value: bool) -> None:
        self._hover = value
        self._draw()

    def _on_release(self, event) -> None:
        if 0 <= event.x <= self._bw and 0 <= event.y <= self._bh:
            self._command()

    def _draw(self) -> None:
        self.delete("all")
        fill = self._hover_bg if self._hover else self._bg
        rounded_rect(self, 1, 1, self._bw - 1, self._bh - 1, 10, fill=fill, outline="")
        self.create_text(self._bw / 2, self._bh / 2, text=self._text, fill=self._fg,
                         font=font(self._size, "bold"))


def make_entry(master, variable: tk.StringVar, width=24) -> tk.Entry:
    return tk.Entry(master, textvariable=variable, width=width, bg=COLORS["input"],
                    fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat",
                    highlightthickness=1, highlightbackground=COLORS["border"],
                    highlightcolor=COLORS["accent"], font=font(10), bd=0)
