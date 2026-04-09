"""Event model for the discrete event simulator."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class EventType(Enum):
    SEND = auto()
    RECEIVE = auto()
    ACK = auto()
    TIMEOUT = auto()
    DROP = auto()


@dataclass(order=True)
class Event:
    time: float
    priority: int
    event_type: EventType = field(compare=False)
    data: Any = field(default=None, compare=False)
