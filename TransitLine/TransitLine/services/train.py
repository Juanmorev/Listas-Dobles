"""Train that moves along the line following next/prev pointers."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from core.node import Node
from services.route import Route


class Direction(Enum):
    FORWARD = "forward"
    BACKWARD = "backward"

    def opposite(self) -> "Direction":
        return Direction.BACKWARD if self is Direction.FORWARD else Direction.FORWARD


class Train:
    """Keeps a pointer to the station where the train currently is."""

    def __init__(self, route: Route) -> None:
        self.route = route
        self.position: Optional[Node] = None
        self.direction = Direction.FORWARD
        self.stops_made = 0

    # ------------------------------------------------------------ placement
    def place_at(self, node: Optional[Node]) -> None:
        self.position = node

    def release(self, node: Node) -> None:
        """Call before removing `node`: the train moves to a neighbour station."""
        if node is self.position:
            self.position = node.next or node.prev

    def reset(self) -> None:
        self.position = None
        self.direction = Direction.FORWARD
        self.stops_made = 0

    # ------------------------------------------------------------- movement
    def ahead(self) -> Optional[Node]:
        """Station the train reaches next in its current direction."""
        if self.position is None:
            return None
        if self.direction is Direction.FORWARD:
            return self.position.next
        return self.position.prev

    def behind(self) -> Optional[Node]:
        if self.position is None:
            return None
        if self.direction is Direction.FORWARD:
            return self.position.prev
        return self.position.next

    def move_forward(self) -> Optional[Node]:
        """Follow `next`. Returns None when the tail is reached."""
        return self._move(self.position.next if self.position else None)

    def move_backward(self) -> Optional[Node]:
        """Follow `prev`. Returns None when the head is reached."""
        return self._move(self.position.prev if self.position else None)

    def step(self) -> Optional[Node]:
        """Automatic movement: bounce at the terminals like a real line."""
        if self.position is None:
            self.position = self.route.stations.head
            return self.position
        if self.ahead() is None:
            self.direction = self.direction.opposite()
        target = self.ahead()
        return self._move(target) if target is not None else self.position

    def reverse_direction(self) -> None:
        self.direction = self.direction.opposite()

    def _move(self, target: Optional[Node]) -> Optional[Node]:
        if target is None:
            return None
        self.position = target
        self.stops_made += 1
        return target
