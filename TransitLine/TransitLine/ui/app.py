"""Main window of TransitLine."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional

from core.node import Node
from data.sample_line import SAMPLE_STATIONS
from models.station import Station
from services.route import Route
from services.train import Direction, Train
from ui.dialogs import AddStationDialog
from ui.line_map import LineMap
from ui.list_diagram import LinkedListDiagram, short
from ui.theme import COLORS, apply_ttk_styles, font
from ui.widgets import RoundedButton

C = COLORS
SPEEDS = [("Slow", 1500), ("Normal", 800), ("Fast", 300)]


class TransitApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TransitLine · Doubly linked list route manager")
        width = min(1320, self.winfo_screenwidth() - 40)
        height = min(900, self.winfo_screenheight() - 80)
        self.geometry(f"{width}x{height}")
        self.minsize(1100, 600)
        self.configure(bg=C["bg"])
        apply_ttk_styles(self)

        self.route = Route("Line 1")
        self.train = Train(self.route)
        self._row_nodes: Dict[str, Node] = {}
        self._name_nodes: Dict[str, Node] = {}
        self._path: set = set()
        self._auto_job: Optional[str] = None
        self._auto_on = False
        self._speed_index = 1

        self._compact = self.winfo_screenheight() < 860
        self._show_table = False
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._build_statusbar()
        self.bind("<Left>", lambda _e: self._guard_keys(self._move_backward))
        self.bind("<Right>", lambda _e: self._guard_keys(self._move_forward))
        self.bind("<Delete>", lambda _e: self._guard_keys(self._remove_selected))
        self._load_sample()

    # ------------------------------------------------------------------ layout
    def _build_sidebar(self) -> None:
        sb = tk.Frame(self, bg=C["sidebar"], width=268)
        sb.grid(row=0, column=0, sticky="ns")
        sb.pack_propagate(False)
        title = tk.Frame(sb, bg=C["sidebar"])
        title.pack(anchor="w", padx=22, pady=(20, 2))
        tk.Label(title, text="Transit", bg=C["sidebar"], fg=C["text"], font=font(21, "bold")).pack(side="left")
        tk.Label(title, text="Line", bg=C["sidebar"], fg=C["accent"], font=font(21, "bold")).pack(side="left")
        tk.Label(sb, text="Manage a transit line stored as a doubly linked list.",
                 bg=C["sidebar"], fg=C["muted"], font=font(9), wraplength=222,
                 justify="left").pack(anchor="w", padx=22, pady=(0, 8))

        self._section(sb, "Edit the line")
        for text, command, kind in [
            ("Add station…", self._add_station, "primary"),
            ("Remove selected", self._remove_selected, "danger"),
            ("Move earlier", lambda: self._shift_selected(-1), "secondary"),
            ("Move later", lambda: self._shift_selected(1), "secondary"),
            ("Reverse the line", self._reverse_line, "secondary"),
        ]:
            RoundedButton(sb, text, command, 224, 34, kind).pack(padx=22, pady=2)
        self._section(sb, "Line data")
        RoundedButton(sb, "Load sample line", self._load_sample, 224, 34, "secondary").pack(padx=22, pady=2)
        RoundedButton(sb, "Clear line", self._clear_line, 224, 34, "secondary").pack(padx=22, pady=2)
        if self._compact:
            self.view_btn = RoundedButton(sb, "Show stations table", self._toggle_view, 224, 34, "primary")
            self.view_btn.pack(padx=22, pady=(10, 2))

        self._section(sb, "List state")
        info = tk.Frame(sb, bg=C["sidebar"])
        info.pack(fill="x", padx=22)
        self.info: Dict[str, tk.Label] = {}
        for key, label in [("length", "length"), ("time", "end to end"), ("head", "head"),
                           ("tail", "tail"), ("train", "train at")]:
            row = tk.Frame(info, bg=C["sidebar"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, bg=C["sidebar"], fg=C["muted"], font=font(9)).pack(side="left")
            self.info[key] = tk.Label(row, text="-", bg=C["sidebar"], fg=C["text"], font=font(9, "bold"))
            self.info[key].pack(side="right")

    def _section(self, parent, text: str) -> None:
        tk.Label(parent, text=text, bg=C["sidebar"], fg=C["muted"], font=font(9, "bold")
                 ).pack(anchor="w", padx=22, pady=(12, 5))

    def _card(self, parent, row: int, weight: int = 0, pady=(0, 14)) -> tk.Frame:
        frame = tk.Frame(parent, bg=C["card"])
        frame.grid(row=row, column=0, sticky="nsew", pady=pady)
        parent.rowconfigure(row, weight=weight)
        return frame

    def _build_main(self) -> None:
        main = tk.Frame(self, bg=C["bg"])
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=(18, 8))
        main.columnconfigure(0, weight=1)
        self._build_train_card(self._card(main, 0, pady=(0, 10)))
        if self._compact:
            self.table_card = self._card(main, 1, weight=1, pady=(0, 0))
            self.diagram_card = self._card(main, 1, weight=1, pady=(0, 0))
            self._build_table_card(self.table_card)
            self._build_diagram_card(self.diagram_card)
            self.table_card.grid_remove()
        else:
            self._build_table_card(self._card(main, 1, weight=1, pady=(0, 10)))
            self._build_diagram_card(self._card(main, 2, pady=(0, 0)))
            main.rowconfigure(1, minsize=150)

    def _build_train_card(self, card: tk.Frame) -> None:
        self.line_map = LineMap(card, self._on_station_click)
        self.line_map.pack(fill="x", padx=14, pady=(10, 0))

        bottom = tk.Frame(card, bg=C["card"])
        bottom.pack(fill="x", padx=18, pady=(0, 12))
        left = tk.Frame(bottom, bg=C["card"])
        left.pack(side="left", fill="x", expand=True)
        self.train_title = tk.Label(left, text="", bg=C["card"], fg=C["text"], font=font(17, "bold"))
        self.train_title.pack(anchor="w")
        self.train_sub = tk.Label(left, text="", bg=C["card"], fg=C["muted"], font=font(10))
        self.train_sub.pack(anchor="w", pady=(0, 0))
        self.train_ptrs = tk.Label(left, text="", bg=C["card"], fg=C["muted"], font=font(9))
        self.train_ptrs.pack(anchor="w", pady=(2, 6))
        controls = tk.Frame(left, bg=C["card"])
        controls.pack(anchor="w")
        for text, cmd, kind, w in [("◀  Back", self._move_backward, "secondary", 92),
                                   ("Forward  ▶", self._move_forward, "secondary", 108),
                                   ("Flip direction", self.train_flip, "secondary", 118)]:
            RoundedButton(controls, text, cmd, w, 36, kind, C["card"]).pack(side="left", padx=(0, 8))
        self.auto_btn = RoundedButton(controls, "Auto run", self._toggle_auto, 100, 36, "primary", C["card"])
        self.auto_btn.pack(side="left", padx=(0, 8))
        self.speed_btn = RoundedButton(controls, "Speed: Normal", self._cycle_speed, 124, 36, "secondary", C["card"])
        self.speed_btn.pack(side="left")

        planner = tk.Frame(bottom, bg=C["card_alt"])
        planner.pack(side="right", padx=(24, 0), ipadx=14, ipady=10)
        tk.Label(planner, text="Trip planner", bg=C["card_alt"], fg=C["text"],
                 font=font(11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        self.from_var, self.to_var = tk.StringVar(), tk.StringVar()
        self.from_box = ttk.Combobox(planner, textvariable=self.from_var, state="readonly",
                                     style="Dark.TCombobox", width=17)
        self.to_box = ttk.Combobox(planner, textvariable=self.to_var, state="readonly",
                                   style="Dark.TCombobox", width=17)
        tk.Label(planner, text="From", bg=C["card_alt"], fg=C["muted"], font=font(9)).grid(row=1, column=0, sticky="w")
        self.from_box.grid(row=1, column=1, padx=8, pady=3)
        tk.Label(planner, text="To", bg=C["card_alt"], fg=C["muted"], font=font(9)).grid(row=2, column=0, sticky="w")
        self.to_box.grid(row=2, column=1, padx=8, pady=3)
        RoundedButton(planner, "Plan", self._plan_trip, 70, 56, "primary", C["card_alt"]).grid(
            row=1, column=2, rowspan=2, padx=(0, 4))
        self.trip_label = tk.Label(planner, text="Pick two stations.", bg=C["card_alt"], fg=C["muted"],
                                   font=font(9), wraplength=330, justify="left")
        self.trip_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _build_table_card(self, card: tk.Frame) -> None:
        header = tk.Frame(card, bg=C["card"])
        header.pack(fill="x", padx=18, pady=(10, 6))
        tk.Label(header, text="Stations", bg=C["card"], fg=C["text"], font=font(12, "bold")).pack(side="left")
        tk.Label(header, text="Double-click a row to move the train there.", bg=C["card"],
                 fg=C["muted"], font=font(9)).pack(side="left", padx=14)
        wrap = tk.Frame(card, bg=C["card"])
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        columns = ("index", "name", "zone", "stop", "transfer", "prev", "next")
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings", selectmode="browse", height=3)
        for key, text, width, anchor in [("index", "Index", 60, "center"), ("name", "Station", 190, "w"),
                                         ("zone", "Zone", 60, "center"), ("stop", "Stop (min)", 90, "center"),
                                         ("transfer", "Transfer", 80, "center"), ("prev", "prev pointer", 170, "w"),
                                         ("next", "next pointer", 170, "w")]:
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width, anchor=anchor)
        bar = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview, style="Dark.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=bar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.tree.tag_configure("train", background=C["accent_dark"], foreground=C["accent"])
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._on_select())
        self.tree.bind("<Double-1>", self._on_tree_double)

    def _build_diagram_card(self, card: tk.Frame) -> None:
        header = tk.Frame(card, bg=C["card"])
        header.pack(fill="x", padx=18, pady=(10, 0))
        tk.Label(header, text="Linked list in memory", bg=C["card"], fg=C["text"],
                 font=font(12, "bold")).pack(side="left")
        for color, text in [(C["next"], "next pointer"), (C["prev"], "prev pointer")]:
            tk.Label(header, text=f"●  {text}", bg=C["card"], fg=color, font=font(9)).pack(side="right", padx=(14, 0))
        self.diagram = LinkedListDiagram(card, self._on_station_click, self._place_train_at)
        self.diagram.pack(fill="x", padx=14, pady=(0, 6))
        self.forward_label = tk.Label(card, bg=C["card"], fg=C["muted"], font=font(9), anchor="w")
        self.forward_label.pack(fill="x", padx=18)
        self.backward_label = tk.Label(card, bg=C["card"], fg=C["muted"], font=font(9), anchor="w")
        self.backward_label.pack(fill="x", padx=18, pady=(0, 8))

    def _build_statusbar(self) -> None:
        self.status = tk.Label(self, text="", bg=C["panel"], fg=C["muted"], font=font(9), anchor="w", padx=18, pady=7)
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew")

    # ------------------------------------------------------------------ helpers
    def _toggle_view(self) -> None:
        self._show_table = not self._show_table
        if self._show_table:
            self.diagram_card.grid_remove()
            self.table_card.grid()
            self.view_btn.set_text("Show memory view")
        else:
            self.table_card.grid_remove()
            self.diagram_card.grid()
            self.view_btn.set_text("Show stations table")

    def _say(self, text: str, error: bool = False) -> None:
        self.status.config(text=text, fg=C["danger"] if error else C["muted"])

    def _guard_keys(self, action) -> None:
        if not isinstance(self.focus_get(), (tk.Entry, tk.Spinbox, ttk.Combobox)):
            action()

    def _selected(self) -> Optional[Node]:
        selection = self.tree.selection()
        return self._row_nodes.get(selection[0]) if selection else None

    def _select(self, node: Optional[Node]) -> None:
        if node is not None and str(id(node)) in self._row_nodes:
            self.tree.selection_set(str(id(node)))
            self.tree.see(str(id(node)))
        self._on_select()

    # ----------------------------------------------------------------- refresh
    def _refresh_all(self) -> None:
        selected = self._selected()
        self._refresh_table()
        if selected is not None and str(id(selected)) in self._row_nodes:
            self.tree.selection_set(str(id(selected)))
        self._refresh_planner()
        self._refresh_visuals()
        self._refresh_info()

    def _refresh_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self._row_nodes.clear()
        for index, node in enumerate(self.route.stations.nodes()):
            s = node.value
            iid = str(id(node))
            self._row_nodes[iid] = node
            self.tree.insert("", "end", iid=iid, tags=("train",) if node is self.train.position else (),
                             values=(index, s.name, s.zone, s.stop_minutes, "Yes" if s.transfer else "-",
                                     node.prev.value.name if node.prev else "None",
                                     node.next.value.name if node.next else "None"))

    def _refresh_planner(self) -> None:
        names = [n.value.name for n in self.route.stations.nodes()]
        self._name_nodes = {n.value.name: n for n in self.route.stations.nodes()}
        self.from_box.config(values=names)
        self.to_box.config(values=names)
        for var in (self.from_var, self.to_var):
            if var.get() not in self._name_nodes:
                var.set("")

    def _on_select(self) -> None:
        self._refresh_visuals()

    def _refresh_visuals(self) -> None:
        selected = self._selected()
        position = self.train.position
        forward = self.train.direction is Direction.FORWARD
        self.line_map.render(self.route, position, forward, selected, self._path)
        self.diagram.render(self.route.stations, position, selected, self._path)
        self._refresh_train_card()
        stations = self.route.stations
        names = lambda it: "  →  ".join(short(n.value.name, 14) for n in it) or "(empty)"
        self.forward_label.config(text="forward  (head → tail via next):   " + short(names(stations.nodes()), 150))
        self.backward_label.config(text="backward (tail → head via prev):   " + short(names(stations.nodes_reversed()), 150))

    def _refresh_train_card(self) -> None:
        position = self.train.position
        forward = self.train.direction is Direction.FORWARD
        if position is None:
            self.train_title.config(text="Train not on the line")
            self.train_sub.config(text="Add stations, then use Forward or Auto run to start.")
            self.train_ptrs.config(text="")
            return
        ahead = self.train.ahead()
        self.train_title.config(text=position.value.name)
        arrow = "▶ forward" if forward else "◀ backward"
        target = ahead.value.name if ahead else "terminal, will turn around"
        self.train_sub.config(text=f"Heading {arrow}  ·  next stop: {target}  ·  stops made: {self.train.stops_made}")
        prev_n = position.prev.value.name if position.prev else "None"
        next_n = position.next.value.name if position.next else "None"
        self.train_ptrs.config(text=f"current.prev = {prev_n}      current.next = {next_n}")

    def _refresh_info(self) -> None:
        stations = self.route.stations
        self.info["length"].config(text=str(len(stations)))
        self.info["time"].config(text=f"{self.route.total_minutes()} min")
        self.info["head"].config(text=short(stations.head.value.name, 16) if stations.head else "None")
        self.info["tail"].config(text=short(stations.tail.value.name, 16) if stations.tail else "None")
        pos = self.train.position
        self.info["train"].config(text=short(pos.value.name, 16) if pos else "None")

    # ----------------------------------------------------------------- editing
    def _add_station(self) -> None:
        names = {s.name for s in self.route.stations}
        dialog = AddStationDialog(self, len(self.route), names)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        station, position = dialog.result
        node = self.route.add_station(station, position)
        if self.train.position is None:
            self.train.place_at(self.route.stations.head)
        self._path.clear()
        self._refresh_all()
        self._select(node)
        where = {"start": "as the new head", "end": "as the new tail"}.get(position, f"at index {position}")
        self._say(f"'{station.name}' linked {where}. Neighbour pointers were updated.")

    def _remove_selected(self) -> None:
        node = self._selected()
        if node is None:
            self._say("Select a station first.", True)
            return
        name = node.value.name
        self.train.release(node)
        self.route.remove_station(node)
        self._path.clear()
        self._refresh_all()
        self._say(f"'{name}' removed: its neighbours now point to each other.")

    def _shift_selected(self, offset: int) -> None:
        node = self._selected()
        if node is None:
            self._say("Select a station first.", True)
            return
        if not self.route.move_station(node, offset):
            self._say("That station is already at the end of the line.", True)
            return
        self._path.clear()
        self._refresh_all()
        self._select(node)
        self._say(f"'{node.value.name}' moved to index {self.route.stations.index_of(node)}.")

    def _reverse_line(self) -> None:
        if len(self.route) < 2:
            self._say("Add at least two stations to reverse the line.", True)
            return
        self.route.reverse()
        self._path.clear()
        self._refresh_all()
        self._say(f"Every node swapped next and prev. New head: {self.route.stations.head.value.name}.")

    def _load_sample(self) -> None:
        self._stop_auto()
        self.route.clear()
        for name, zone, stop, transfer in SAMPLE_STATIONS:
            self.route.add_station(Station(name, zone, stop, transfer))
        self.train.reset()
        self.train.place_at(self.route.stations.head)
        self._path.clear()
        self.trip_label.config(text="Pick two stations.", fg=C["muted"])
        self._refresh_all()
        self._say("Sample line loaded: 8 stations linked with next and prev pointers.")

    def _clear_line(self) -> None:
        if len(self.route) and not messagebox.askyesno("Clear line", "Remove every station from the line?"):
            return
        self._stop_auto()
        self.route.clear()
        self.train.reset()
        self._path.clear()
        self._refresh_all()
        self._say("The line is empty: head and tail are None.")

    # ------------------------------------------------------------------- train
    def _ensure_train(self) -> bool:
        if self.route.stations.head is None:
            self._say("Add stations before running the train.", True)
            return False
        if self.train.position is None:
            self.train.place_at(self.route.stations.head)
        return True

    def _move_forward(self) -> None:
        if not self._ensure_train():
            return
        if self.train.move_forward() is None:
            self._say("End of the line: the tail has no next pointer.", True)
        else:
            self.train.direction = Direction.FORWARD
        self._refresh_all()

    def _move_backward(self) -> None:
        if not self._ensure_train():
            return
        if self.train.move_backward() is None:
            self._say("Start of the line: the head has no prev pointer.", True)
        else:
            self.train.direction = Direction.BACKWARD
        self._refresh_all()

    def train_flip(self) -> None:
        self.train.reverse_direction()
        self._refresh_visuals()
        self._say(f"Train now heads {self.train.direction.value}.")

    def _toggle_auto(self) -> None:
        if self._auto_on:
            self._stop_auto()
            self._say("Auto run stopped.")
        elif self._ensure_train():
            self._auto_on = True
            self.auto_btn.set_text("Stop")
            self._say("Auto run: the train follows next or prev and turns around at the terminals.")
            self._schedule_auto()

    def _stop_auto(self) -> None:
        self._auto_on = False
        if self._auto_job is not None:
            self.after_cancel(self._auto_job)
            self._auto_job = None
        self.auto_btn.set_text("Auto run")

    def _schedule_auto(self) -> None:
        self._auto_job = self.after(SPEEDS[self._speed_index][1], self._auto_step)

    def _auto_step(self) -> None:
        if not self._auto_on:
            return
        self.train.step()
        self._refresh_all()
        self._schedule_auto()

    def _cycle_speed(self) -> None:
        self._speed_index = (self._speed_index + 1) % len(SPEEDS)
        self.speed_btn.set_text(f"Speed: {SPEEDS[self._speed_index][0]}")

    def _place_train_at(self, node: Node) -> None:
        self.train.place_at(node)
        self._refresh_all()
        self._say(f"Train placed at '{node.value.name}'.")

    def _on_tree_double(self, event) -> None:
        row = self.tree.identify_row(event.y)
        if row in self._row_nodes:
            self._place_train_at(self._row_nodes[row])

    def _on_station_click(self, node: Node) -> None:
        self._select(node)

    # ------------------------------------------------------------------ planner
    def _plan_trip(self) -> None:
        origin = self._name_nodes.get(self.from_var.get())
        destination = self._name_nodes.get(self.to_var.get())
        if origin is None or destination is None:
            self.trip_label.config(text="Choose an origin and a destination.", fg=C["danger"])
            return
        trip = self.route.plan_trip(origin, destination)
        self._path = {id(n) for n in trip.stops}
        route_text = "  →  ".join(short(n.value.name, 12) for n in trip.stops)
        if trip.hops == 0:
            self.trip_label.config(text="You are already at that station.", fg=C["green"])
        else:
            self.trip_label.config(
                text=f"{trip.direction.capitalize()} · {trip.hops} hops · {trip.minutes} min\n{route_text}",
                fg=C["green"])
        self._refresh_visuals()
        self._say(f"Trip found by following {'next' if trip.direction == 'forward' else 'prev'} pointers.")
