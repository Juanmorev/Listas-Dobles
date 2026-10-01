"""Colors, fonts and ttk styling shared by every widget."""
from __future__ import annotations

import sys
from tkinter import ttk

COLORS = {
    "bg": "#0c141d",
    "sidebar": "#0f1a26",
    "panel": "#142130",
    "card": "#182a3c",
    "card_alt": "#1f3449",
    "border": "#2b4660",
    "input": "#0e1822",
    "text": "#e8f1f8",
    "muted": "#8ea6bb",
    "accent": "#ffb400",       # line yellow
    "accent_hover": "#ffc83d",
    "accent_dark": "#4a3a0a",
    "next": "#38bdf8",         # next pointer
    "prev": "#fb7185",         # prev pointer
    "green": "#34d399",
    "danger": "#f43f5e",
    "danger_dim": "#3a1c28",
    "on_accent": "#1a1300",
}

ZONE_COLORS = {"A": "#38bdf8", "B": "#34d399", "C": "#c084fc", "D": "#fb923c"}

if sys.platform.startswith("win"):
    FONT_FAMILY = "Segoe UI"
elif sys.platform == "darwin":
    FONT_FAMILY = "Helvetica Neue"
else:
    FONT_FAMILY = "DejaVu Sans"


def font(size: int, weight: str = "normal"):
    return (FONT_FAMILY, size, weight)


def blend(color_a: str, color_b: str, t: float) -> str:
    """Mix two #rrggbb colors; t=0 gives color_a, t=1 gives color_b."""
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    mixed = [round(x + (y - x) * t) for x, y in zip(a, b)]
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def zone_color(zone: str) -> str:
    return ZONE_COLORS.get(zone.strip().upper()[:1], COLORS["muted"])


def apply_ttk_styles(root) -> None:
    c = COLORS
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Treeview", background=c["card"], fieldbackground=c["card"],
                    foreground=c["text"], rowheight=30, borderwidth=0, font=font(10))
    style.configure("Treeview.Heading", background=c["panel"], foreground=c["muted"],
                    relief="flat", borderwidth=0, font=font(9, "bold"), padding=(8, 7))
    style.map("Treeview", background=[("selected", c["card_alt"])],
              foreground=[("selected", c["text"])])
    style.map("Treeview.Heading", background=[("active", c["panel"])])
    for orient in ("Vertical", "Horizontal"):
        style.configure(f"Dark.{orient}.TScrollbar", background=c["border"],
                        troughcolor=c["card"], bordercolor=c["card"],
                        arrowcolor=c["muted"], lightcolor=c["border"],
                        darkcolor=c["border"], relief="flat")
        style.map(f"Dark.{orient}.TScrollbar", background=[("active", c["muted"])])
    style.configure("Dark.TCombobox", fieldbackground=c["input"], background=c["card_alt"],
                    foreground=c["text"], arrowcolor=c["text"], bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"], padding=5)
    style.map("Dark.TCombobox", fieldbackground=[("readonly", c["input"])],
              foreground=[("readonly", c["text"])],
              selectbackground=[("readonly", c["input"])],
              selectforeground=[("readonly", c["text"])])
    root.option_add("*TCombobox*Listbox.background", c["input"])
    root.option_add("*TCombobox*Listbox.foreground", c["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", c["on_accent"])
    root.option_add("*TCombobox*Listbox.font", font(10))
