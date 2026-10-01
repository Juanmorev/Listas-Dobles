"""Generic doubly linked list built only with nodes and pointers."""
from __future__ import annotations

from typing import Callable, Generic, Iterator, Optional, TypeVar

from core.node import Node

T = TypeVar("T")


class DoublyLinkedList(Generic[T]):
    """Doubly linked list with head, tail and length.

    Every operation works by rewiring `next` and `prev` pointers; no Python
    list is used to store the elements.
    """

    def __init__(self) -> None:
        self.head: Optional[Node[T]] = None
        self.tail: Optional[Node[T]] = None
        self.length: int = 0

    # ------------------------------------------------------------------ basics
    def __len__(self) -> int:
        return self.length

    def __iter__(self) -> Iterator[T]:
        for node in self.nodes():
            yield node.value

    def __reversed__(self) -> Iterator[T]:
        for node in self.nodes_reversed():
            yield node.value

    def is_empty(self) -> bool:
        return self.length == 0

    def nodes(self) -> Iterator[Node[T]]:
        """Walk from head to tail following `next`."""
        current = self.head
        while current is not None:
            yield current
            current = current.next

    def nodes_reversed(self) -> Iterator[Node[T]]:
        """Walk from tail to head following `prev`."""
        current = self.tail
        while current is not None:
            yield current
            current = current.prev

    # --------------------------------------------------------------- insertion
    def append(self, value: T) -> Node[T]:
        """Add a value at the end."""
        node = Node(value)
        self._attach_tail(node)
        return node

    def prepend(self, value: T) -> Node[T]:
        """Add a value at the start."""
        node = Node(value)
        self._attach_head(node)
        return node

    def insert(self, index: int, value: T) -> Node[T]:
        """Add a value at `index` (clamped to the list bounds)."""
        return self.insert_node(index, Node(value))

    def insert_node(self, index: int, node: Node[T]) -> Node[T]:
        """Link an existing node at `index`, keeping its identity."""
        if index <= 0 or self.head is None:
            self._attach_head(node)
        elif index >= self.length:
            self._attach_tail(node)
        else:
            follower = self.node_at(index)
            leader = follower.prev
            node.prev = leader
            node.next = follower
            leader.next = node
            follower.prev = node
            self.length += 1
        return node

    def _attach_head(self, node: Node[T]) -> None:
        if self.head is None:
            self.head = self.tail = node
            node.prev = node.next = None
        else:
            node.prev = None
            node.next = self.head
            self.head.prev = node
            self.head = node
        self.length += 1

    def _attach_tail(self, node: Node[T]) -> None:
        if self.tail is None:
            self.head = self.tail = node
            node.prev = node.next = None
        else:
            node.next = None
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self.length += 1

    # ----------------------------------------------------------------- removal
    def remove_node(self, node: Node[T]) -> T:
        """Unlink a node in O(1) thanks to the `prev` pointer."""
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        node.next = node.prev = None
        self.length -= 1
        return node.value

    def remove_at(self, index: int) -> T:
        return self.remove_node(self.node_at(index))

    def clear(self) -> None:
        """Break every link and empty the list."""
        for node in list(self.nodes()):
            node.next = node.prev = None
        self.head = self.tail = None
        self.length = 0

    # ------------------------------------------------------------------ access
    def node_at(self, index: int) -> Node[T]:
        """Return the node at `index`, starting from the closest end."""
        if not 0 <= index < self.length:
            raise IndexError(f"Index {index} is out of range (length {self.length})")
        if index <= self.length // 2:
            current = self.head
            for _ in range(index):
                current = current.next
        else:
            current = self.tail
            for _ in range(self.length - 1 - index):
                current = current.prev
        return current

    def index_of(self, node: Node[T]) -> int:
        for position, candidate in enumerate(self.nodes()):
            if candidate is node:
                return position
        raise ValueError("The node does not belong to this list")

    def find(self, predicate: Callable[[T], bool]) -> Optional[Node[T]]:
        for node in self.nodes():
            if predicate(node.value):
                return node
        return None

    # ----------------------------------------------------------- restructuring
    def move(self, from_index: int, to_index: int) -> Node[T]:
        """Move a node to another position without recreating it."""
        if not 0 <= to_index < self.length:
            raise IndexError(f"Index {to_index} is out of range (length {self.length})")
        node = self.node_at(from_index)
        if from_index != to_index:
            self.remove_node(node)
            self.insert_node(to_index, node)
        return node

    def reverse(self) -> None:
        """Reverse the list in place by swapping every node's pointers."""
        current = self.head
        while current is not None:
            current.next, current.prev = current.prev, current.next
            current = current.prev  # the old `next`
        self.head, self.tail = self.tail, self.head
