from simulator.event import Event, EventType
from simulator.event_queue import EventQueue


def test_event_queue_orders_by_time_then_priority():
    queue = EventQueue()
    queue.push(Event(time=2.0, priority=1, event_type=EventType.SEND))
    queue.push(Event(time=1.0, priority=1, event_type=EventType.RECEIVE))
    queue.push(Event(time=1.0, priority=0, event_type=EventType.ACK))

    first = queue.pop()
    second = queue.pop()
    third = queue.pop()

    assert first.event_type == EventType.ACK
    assert second.event_type == EventType.RECEIVE
    assert third.event_type == EventType.SEND
