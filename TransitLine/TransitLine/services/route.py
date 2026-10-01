"""Route: a transit line stored in a doubly linked list of stations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union

from core.doubly_linked_list import DoublyLinkedList
from core.node import Node
from models.station import Station

Position = Union[str, int]  # "start", "end" or an index


@dataclass
class Trip:
    """Result of a trip plan between two stations."""

    direction: str  # "forward" (following next) or "backward" (following prev)
    stops: List[Node] = field(default_factory=list)
    minutes: int = 0

    @property
    def hops(self) -> int:
        return max(0, len(self.stops) - 1)


class Route:
    """A named line whose stations are linked in both directions."""

    HOP_MINUTES = 2  # travel time between two consecutive stations

    def __init__(self, name: str = "Line 1") -> None:
        self.name = name
        self.stations: DoublyLinkedList[Station] = DoublyLinkedList()

    def __len__(self) -> int:
        return len(self.stations)

    # -------------------------------------------------------------- editing
    def has_name(self, name: str) -> bool:
        wanted = name.strip().lower()
        return any(s.name.strip().lower() == wanted for s in self.stations)

    def add_station(self, station: Station, position: Position = "end") -> Node:
        if self.has_name(station.name):
            raise ValueError(f"A station named '{station.name}' already exists")
        if position == "start":
            return self.stations.prepend(station)
        if position == "end":
            return self.stations.append(station)
        return self.stations.insert(int(position), station)

    def remove_station(self, node: Node) -> Station:
        return self.stations.remove_node(node)

    def move_station(self, node: Node, offset: int) -> bool:
        """Shift a station by `offset` positions. Returns False at the edges."""
        index = self.stations.index_of(node)
        target = index + offset
        if not 0 <= target < len(self.stations):
            return False
        self.stations.move(index, target)
        return True

    def reverse(self) -> None:
        self.stations.reverse()

    def clear(self) -> None:
        self.stations.clear()

    # ---------------------------------------------------------------- queries
    def search(self, text: str) -> List[Node]:
        text = text.strip().lower()
        return [n for n in self.stations.nodes() if text in n.value.name.lower()]

    def total_minutes(self) -> int:
        """End-to-end time: hops plus waiting time at intermediate stations."""
        nodes = list(self.stations.nodes())
        if len(nodes) < 2:
            return 0
        return self._minutes_for(nodes)

    def plan_trip(self, origin: Node, destination: Node) -> Trip:
        """Look in both directions at once and follow the pointers that lead there."""
        if origin is destination:
            return Trip("forward", [origin], 0)
        ahead: Optional[Node] = origin
        behind: Optional[Node] = origin
        while ahead is not None or behind is not None:
            if ahead is destination:
                return self._build_trip(origin, destination, "forward")
            if behind is destination:
                return self._build_trip(origin, destination, "backward")
            ahead = ahead.next if ahead is not None else None
            behind = behind.prev if behind is not None else None
        raise ValueError("The stations do not belong to this line")

    def _build_trip(self, origin: Node, destination: Node, direction: str) -> Trip:
        stops = [origin]
        current = origin
        while current is not destination:
            current = current.next if direction == "forward" else current.prev
            stops.append(current)
        return Trip(direction, stops, self._minutes_for(stops))

    def _minutes_for(self, stops: List[Node]) -> int:
        waiting = sum(n.value.stop_minutes for n in stops[1:-1])
        return (len(stops) - 1) * self.HOP_MINUTES + waiting
