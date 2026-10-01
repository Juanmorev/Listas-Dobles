"""Memory view of the doubly linked list: nodes, prev/next pointers, head and tail."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Set

from core.doubly_linked_list import DoublyLinkedList
from core.node import Node
from models.station import Station
from ui.theme import COLORS, blend, font
from ui.widgets import rounded_rect


def short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit - 1] + "…"


class LinkedListDiagram(tk.Frame):
    NODE_W, GAP, NULL_W, PAD, TOP = 176, 72, 58, 26, 50
    ROWS = (24, 42, 24)

    def __init__(self, master, on_click: Callable[[Node], None],
                 on_double_click: Callable[[Node], None]):
        super().__init__(master, bg=COLORS["card"])
        self._on_click, self._on_double = on_click, on_double_click
        self.canvas = tk.Canvas(self, bg=COLORS["card"], highlightthickness=0, height=178)
        bar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview,
                            style="Dark.Horizontal.TScrollbar")
        self.canvas.configure(xscrollcommand=bar.set)
        self.canvas.pack(fill="both", expand=True)
        bar.pack(fill="x")
        self._last_focus: Optional[Node] = None

    def render(self, nodes_list: DoublyLinkedList[Station], train: Optional[Node],
               selected: Optional[Node], path: Set[int]) -> None:
        c = self.canvas
        c.delete("all")
        nodes = list(nodes_list.nodes())
        if not nodes:
            c.create_text(30, 80, anchor="w", fill=COLORS["muted"], font=font(11),
                          text="head = None    tail = None    length = 0")
            c.configure(scrollregion=(0, 0, 400, 170))
            return

        h1, h2, h3 = self.ROWS
        height = h1 + h2 + h3
        y_prev = self.TOP + h1 / 2
        y_next = self.TOP + h1 + h2 + h3 / 2
        positions, x = [], self.PAD + self.NULL_W + self.GAP
        for _ in nodes:
            positions.append(x)
            x += self.NODE_W + self.GAP
        total_w = x - self.GAP + self.GAP + self.NULL_W + self.PAD

        self._null_box(self.PAD, y_prev)
        c.create_line(positions[0], y_prev, self.PAD + self.NULL_W, y_prev, arrow="last",
                      fill=COLORS["prev"], width=2)
        tail_x = positions[-1] + self.NODE_W
        self._null_box(tail_x + self.GAP, y_next)
        c.create_line(tail_x, y_next, tail_x + self.GAP, y_next, arrow="last",
                      fill=COLORS["next"], width=2)

        for i in range(len(nodes) - 1):
            right, left = positions[i] + self.NODE_W, positions[i + 1]
            c.create_line(right, y_next, left, y_next, arrow="last", fill=COLORS["next"], width=2)
            c.create_line(left, y_prev, right, y_prev, arrow="last", fill=COLORS["prev"], width=2)

        for i, node in enumerate(nodes):
            self._draw_node(positions[i], i, node, node is train, node is selected,
                            id(node) in path, node is nodes_list.head, node is nodes_list.tail,
                            height)
        c.configure(scrollregion=(0, 0, total_w, 170))

        if train is not self._last_focus and train in nodes:
            center = positions[nodes.index(train)] + self.NODE_W / 2
            view = max(c.winfo_width(), 1)
            c.xview_moveto(max(0.0, (center - view / 2) / total_w))
        self._last_focus = train

    def _null_box(self, x: float, y: float) -> None:
        rounded_rect(self.canvas, x, y - 14, x + self.NULL_W, y + 14, 7,
                     fill=COLORS["bg"], outline=COLORS["border"])
        self.canvas.create_text(x + self.NULL_W / 2, y, text="None", fill=COLORS["muted"],
                                font=font(9, "bold"))

    def _draw_node(self, x, index, node, is_train, is_selected, in_path, is_head, is_tail, height):
        c, W, y = self.canvas, self.NODE_W, self.TOP
        h1, h2, h3 = self.ROWS
        tag = f"node{index}"
        station = node.value
        if is_train:
            outline, width = COLORS["accent"], 3
        elif is_selected:
            outline, width = COLORS["next"], 3
        elif in_path:
            outline, width = COLORS["green"], 3
        else:
            outline, width = COLORS["border"], 1
        c.create_rectangle(x, y, x + W, y + h1, fill=blend(COLORS["card"], COLORS["prev"], 0.2),
                           outline="", tags=tag)
        c.create_rectangle(x, y + h1, x + W, y + h1 + h2,
                           fill=COLORS["accent_dark"] if is_train else COLORS["card_alt"],
                           outline="", tags=tag)
        c.create_rectangle(x, y + h1 + h2, x + W, y + height,
                           fill=blend(COLORS["card"], COLORS["next"], 0.2), outline="", tags=tag)
        c.create_rectangle(x, y, x + W, y + height, outline=outline, width=width, tags=tag)
        prev_name = short(node.prev.value.name, 15) if node.prev else "None"
        next_name = short(node.next.value.name, 15) if node.next else "None"
        c.create_text(x + 8, y + h1 / 2, anchor="w", text=f"prev → {prev_name}",
                      fill=COLORS["prev"], font=font(8), tags=tag)
        c.create_text(x + W / 2, y + h1 + 14, text=short(station.name, 19),
                      fill=COLORS["text"], font=font(10, "bold"), tags=tag)
        c.create_text(x + W / 2, y + h1 + 31, text=f"zone {station.zone} · {station.stop_minutes} min stop",
                      fill=COLORS["muted"], font=font(8), tags=tag)
        c.create_text(x + 8, y + h1 + h2 + h3 / 2, anchor="w", text=f"next → {next_name}",
                      fill=COLORS["next"], font=font(8), tags=tag)

        label = f"index {index}" + ("   ● train here" if is_train else "")
        c.create_text(x + W / 2, y + height + 16, text=label,
                      fill=COLORS["accent"] if is_train else COLORS["muted"], font=font(8, "bold"))
        if is_head:
            self._pill(x, y - 28, "HEAD", COLORS["accent"])
        if is_tail:
            self._pill(x + W - 48, y - 28, "TAIL", COLORS["green"])
        c.tag_bind(tag, "<Button-1>", lambda _e, n=node: self._on_click(n))
        c.tag_bind(tag, "<Double-Button-1>", lambda _e, n=node: self._on_double(n))
        c.tag_bind(tag, "<Enter>", lambda _e: c.config(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda _e: c.config(cursor=""))

    def _pill(self, x: float, y: float, text: str, color: str) -> None:
        rounded_rect(self.canvas, x, y, x + 48, y + 18, 8, fill=color, outline="")
        self.canvas.create_text(x + 24, y + 9, text=text, fill=COLORS["on_accent"], font=font(8, "bold"))
        self.canvas.create_line(x + 24, y + 18, x + 24, y + 28, fill=color, width=2)
