"""Node used by the doubly linked list."""
from __future__ import annotations

from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    """A single node: one value and two pointers (next and prev)."""

    def __init__(self, value: T) -> None:
        self.value: T = value
        self.next: Optional[Node[T]] = None  # pointer to the following node
        self.prev: Optional[Node[T]] = None  # pointer to the previous node

    def __repr__(self) -> str:
        return f"Node({self.value!r})"
