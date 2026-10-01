"""Modal dialog used to create a station."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Set, Tuple, Union

from models.station import Station
from ui.theme import COLORS, font
from ui.widgets import RoundedButton, make_entry


class AddStationDialog(tk.Toplevel):
    """Collects the station data and the position where it will be linked."""

    ZONES = ["A", "B", "C", "D"]

    def __init__(self, master, list_length: int, existing_names: Set[str]):
        super().__init__(master)
        self.result: Optional[Tuple[Station, Union[str, int]]] = None
        self._length = list_length
        self._existing = {n.strip().lower() for n in existing_names}
        self.title("Add station")
        self.configure(bg=COLORS["panel"], padx=26, pady=22)
        self.resizable(False, False)
        self.transient(master)

        self.name_var = tk.StringVar()
        self.zone_var = tk.StringVar(value="A")
        self.stop_var = tk.StringVar(value="1")
        self.transfer_var = tk.BooleanVar(value=False)
        self.position_var = tk.StringVar(value="end")
        self.index_var = tk.StringVar(value=str(min(1, list_length)))
        self.error_var = tk.StringVar()

        tk.Label(self, text="New station", bg=COLORS["panel"], fg=COLORS["text"],
                 font=font(15, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        self._label("Name", 1)
        self.name_entry = make_entry(self, self.name_var, 30)
        self.name_entry.grid(row=2, column=0, columnspan=2, sticky="ew", ipady=6)
        self._label("Zone", 3)
        self._label("Stop time (minutes)", 3, column=1)
        ttk.Combobox(self, textvariable=self.zone_var, values=self.ZONES, state="readonly",
                     style="Dark.TCombobox", width=8).grid(row=4, column=0, sticky="w", padx=(0, 12))
        tk.Spinbox(self, from_=1, to=10, textvariable=self.stop_var, width=8, bg=COLORS["input"],
                   fg=COLORS["text"], buttonbackground=COLORS["card_alt"], relief="flat",
                   insertbackground=COLORS["text"], font=font(10)).grid(row=4, column=1, sticky="w", ipady=4)
        tk.Checkbutton(self, text="Transfer station", variable=self.transfer_var, bg=COLORS["panel"],
                       fg=COLORS["text"], selectcolor=COLORS["input"], activebackground=COLORS["panel"],
                       activeforeground=COLORS["text"], font=font(10), highlightthickness=0,
                       bd=0).grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))

        self._label("Where in the line?", 6)
        for row, (text, value) in enumerate([("At the start (new head)", "start"),
                                             ("At the end (new tail)", "end"),
                                             ("At a specific index", "index")]):
            tk.Radiobutton(self, text=text, value=value, variable=self.position_var,
                           bg=COLORS["panel"], fg=COLORS["text"], selectcolor=COLORS["input"],
                           activebackground=COLORS["panel"], activeforeground=COLORS["text"],
                           font=font(10), highlightthickness=0, bd=0,
                           command=self._sync_index).grid(row=7 + row, column=0, sticky="w")
        self.index_spin = tk.Spinbox(self, from_=0, to=max(list_length, 0), textvariable=self.index_var,
                                     width=6, bg=COLORS["input"], fg=COLORS["text"],
                                     buttonbackground=COLORS["card_alt"], relief="flat",
                                     insertbackground=COLORS["text"], font=font(10),
                                     disabledbackground=COLORS["panel"], disabledforeground=COLORS["muted"])
        self.index_spin.grid(row=9, column=1, sticky="w", ipady=3)
        self._sync_index()

        tk.Label(self, textvariable=self.error_var, bg=COLORS["panel"], fg=COLORS["danger"],
                 font=font(9), wraplength=340, justify="left").grid(row=10, column=0, columnspan=2,
                                                                    sticky="w", pady=(12, 0))
        buttons = tk.Frame(self, bg=COLORS["panel"])
        buttons.grid(row=11, column=0, columnspan=2, sticky="e", pady=(14, 0))
        RoundedButton(buttons, "Cancel", self.destroy, 100, 36, "secondary",
                      COLORS["panel"]).pack(side="left", padx=(0, 8))
        RoundedButton(buttons, "Add station", self._submit, 130, 36, "primary",
                      COLORS["panel"]).pack(side="left")

        self.bind("<Return>", lambda _e: self._submit())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.name_entry.focus_set()

    def _label(self, text: str, row: int, column: int = 0) -> None:
        tk.Label(self, text=text, bg=COLORS["panel"], fg=COLORS["muted"],
                 font=font(9)).grid(row=row, column=column, sticky="w", pady=(12, 4))

    def _sync_index(self) -> None:
        self.index_spin.config(state="normal" if self.position_var.get() == "index" else "disabled")

    def _submit(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            self.error_var.set("Enter a name for the station.")
            return
        if name.lower() in self._existing:
            self.error_var.set(f"'{name}' already exists. Station names must be unique.")
            return
        try:
            stop = int(self.stop_var.get())
            if stop < 1:
                raise ValueError
        except ValueError:
            self.error_var.set("Stop time must be a whole number of minutes (1 or more).")
            return
        position: Union[str, int] = self.position_var.get()
        if position == "index":
            try:
                position = int(self.index_var.get())
            except ValueError:
                self.error_var.set("The index must be a whole number.")
                return
            if not 0 <= position <= self._length:
                self.error_var.set(f"The index must be between 0 and {self._length}.")
                return
        self.result = (Station(name, self.zone_var.get(), stop, self.transfer_var.get()), position)
        self.destroy()
