"""Priority queue wrapper for simulator events."""

import heapq
from typing import List

from .event import Event


class EventQueue:
    def __init__(self) -> None:
        self._heap: List[Event] = []

    def push(self, event: Event) -> None:
        heapq.heappush(self._heap, event)

    def pop(self) -> Event:
        return heapq.heappop(self._heap)

    def is_empty(self) -> bool:
        return not self._heap

    def __len__(self) -> int:
        return len(self._heap)
