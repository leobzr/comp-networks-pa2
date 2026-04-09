"""Main discrete event simulator loop and scheduling API."""

from .abstractions import BaseReceiver, BaseSender
from .clock import SimulatedClock
from .event import Event, EventType
from .event_queue import EventQueue
from .metrics import MetricsCollector
from .network import Network
from .packet import Ack, Packet


class Simulator:
    def __init__(
        self,
        network: Network,
        metrics: MetricsCollector,
        sender: BaseSender | None = None,
        receiver: BaseReceiver | None = None,
        timeout_interval: float = 1.0,
    ) -> None:
        self.clock = SimulatedClock()
        self.queue = EventQueue()
        self.network = network
        self.metrics = metrics
        self.sender = sender
        self.receiver = receiver
        self.timeout_interval = timeout_interval
        self._acked_packet_ids: set[int] = set()

    def schedule_event(self, time: float, event_type: EventType, data=None, priority: int = 0) -> None:
        # Single entry point for all future work in simulated time.
        self.queue.push(Event(time=time, priority=priority, event_type=event_type, data=data))

    def bind_sender(self, sender: BaseSender) -> None:
        self.sender = sender

    def bind_receiver(self, receiver: BaseReceiver) -> None:
        self.receiver = receiver

    def get_current_time(self) -> float:
        return self.clock.now()

    def _handle_send(self, packet: Packet) -> None:
        # Record transmission, let network decide drop/delivery, and arm timeout.
        now = self.get_current_time()
        self.metrics.record_sent(packet.packet_id, now)
        self.network.send_packet(packet=packet, now=now, schedule_event=self.schedule_event)
        self.schedule_event(now + self.timeout_interval, EventType.TIMEOUT, data=packet.packet_id)

    def _handle_receive(self, packet: Packet) -> None:
        if self.receiver is None:
            return
        now = self.get_current_time()
        # Receiver may provide a custom ACK; fallback to cumulative-style ACK by packet id.
        ack = self.receiver.on_packet_received(packet)
        if ack is None:
            ack = Ack(ack_id=packet.packet_id)
        self.network.send_ack(ack=ack, now=now, schedule_event=self.schedule_event)

    def _handle_ack(self, ack: Ack) -> None:
        self.metrics.record_received(packet_id=ack.ack_id, time=self.get_current_time())
        self._acked_packet_ids.add(ack.ack_id)
        if self.sender is not None:
            self.sender.on_ack_received(ack)

    def _handle_timeout(self, packet_id: int) -> None:
        # Ignore stale timers once packet is already acknowledged.
        if packet_id in self._acked_packet_ids:
            return
        if self.sender is not None:
            self.sender.on_timeout(packet_id)

    def _handle_drop(self, packet: Packet) -> None:
        self.metrics.record_dropped(packet.packet_id)

    def run(self) -> None:
        # Core DES loop: pop earliest event, advance clock, dispatch handler.
        while not self.queue.is_empty():
            event = self.queue.pop()
            self.clock.advance_to(event.time)
            if event.event_type == EventType.SEND:
                self._handle_send(event.data)
            elif event.event_type == EventType.RECEIVE:
                self._handle_receive(event.data)
            elif event.event_type == EventType.ACK:
                self._handle_ack(event.data)
            elif event.event_type == EventType.TIMEOUT:
                self._handle_timeout(event.data)
            elif event.event_type == EventType.DROP:
                self._handle_drop(event.data)
