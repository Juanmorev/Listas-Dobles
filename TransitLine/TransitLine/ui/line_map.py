"""Metro-style map of the line with the train drawn on its current station."""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Set

from core.node import Node
from services.route import Route
from ui.theme import COLORS, font, zone_color
from ui.widgets import rounded_rect


class LineMap(tk.Canvas):
    HEIGHT = 122

    def __init__(self, master, on_station_click: Callable[[Node], None]):
        super().__init__(master, height=self.HEIGHT, bg=COLORS["card"], highlightthickness=0)
        self._on_click = on_station_click
        self._state = None
        self.bind("<Configure>", lambda _e: self._redraw())

    def render(self, route: Route, train: Optional[Node], forward: bool,
               selected: Optional[Node], path: Set[int]) -> None:
        self._state = (route, train, forward, selected, path)
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        if self._state is None:
            return
        route, train, forward, selected, path = self._state
        width = max(self.winfo_width(), 400)
        nodes = list(route.stations.nodes())
        if not nodes:
            self.create_text(width / 2, self.HEIGHT / 2, fill=COLORS["muted"], font=font(11),
                             text="The line is empty. Add a station or load the sample line.")
            return
        pad, y = 70, 62
        count = len(nodes)
        step = (width - 2 * pad) / (count - 1) if count > 1 else 0
        xs = [pad + i * step for i in range(count)] if count > 1 else [width / 2]

        self.create_line(xs[0] - 28, y, xs[-1] + 28, y, width=10, fill=COLORS["accent"],
                         capstyle="round")
        self.create_line(xs[0] - 28, y, xs[-1] + 28, y, width=3,
                         fill=COLORS["accent_hover"], capstyle="round")
        max_chars = max(7, int((step * 1.9) / 6.4)) if count > 1 else 26

        for i, node in enumerate(nodes):
            station, x = node.value, xs[i]
            radius = 12 if station.transfer else 9
            tag = f"st{i}"
            if station.transfer:
                self.create_oval(x - radius - 5, y - radius - 5, x + radius + 5, y + radius + 5,
                                 outline=COLORS["text"], width=1, tags=tag)
            fill = COLORS["green"] if id(node) in path else COLORS["bg"]
            outline = COLORS["next"] if node is selected else zone_color(station.zone)
            self.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill,
                             outline=outline, width=4, tags=tag)
            above = i % 2 == 0
            label = station.name if len(station.name) <= max_chars else station.name[:max_chars - 1] + "…"
            self.create_text(x, y - 30 if above else y + 30, text=label,
                             anchor="s" if above else "n", fill=COLORS["text"],
                             font=font(9, "bold" if node is train else "normal"), tags=tag)
            self.tag_bind(tag, "<Button-1>", lambda _e, n=node: self._on_click(n))
            self.tag_bind(tag, "<Enter>", lambda _e: self.config(cursor="hand2"))
            self.tag_bind(tag, "<Leave>", lambda _e: self.config(cursor=""))

        if train is not None and train in nodes:
            x = xs[nodes.index(train)]
            rounded_rect(self, x - 22, y - 13, x + 22, y + 13, 8, fill=COLORS["text"],
                         outline=COLORS["bg"], width=2)
            self.create_text(x, y, text="▶" if forward else "◀", fill=COLORS["bg"],
                             font=font(11, "bold"))
