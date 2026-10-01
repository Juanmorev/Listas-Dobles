"""Station model."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(eq=False)
class Station:
    """A stop of the line (compared by identity, not by value)."""

    name: str
    zone: str = "A"
    stop_minutes: int = 1  # time the train waits at this station
    transfer: bool = False  # connects with another line
