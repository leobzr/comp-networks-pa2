from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .config import SenderConfig
from .interfaces import MetricsCollectorLike, NetworkLike, SimulatorLike
from .models import PacketRecord


class TCPSender(ABC):
    """Shared sender behavior for Tahoe/Reno without simulator internals."""

    timeout_event_type = "TIMEOUT"

    def __init__(
        self,
        simulator: SimulatorLike,
        network: NetworkLike,
        metrics: MetricsCollectorLike,
        config: SenderConfig,
        name: str,
    ) -> None:
        self.simulator = simulator
        self.network = network
        self.metrics = metrics
        self.config = config
        self.name = name

        self.cwnd = float(config.initial_cwnd)
        self.ssthresh = float(config.initial_ssthresh)

        self._next_packet_id = 1
        self._highest_acked = 0
        self._dup_ack_count = 0
        self._in_flight: set[int] = set()
        self.packet_records: dict[int, PacketRecord] = {}

    @property
    def highest_acked(self) -> int:
        return self._highest_acked

    @property
    def dup_ack_count(self) -> int:
        return self._dup_ack_count

    @property
    def in_flight(self) -> set[int]:
        return set(self._in_flight)

    def is_complete(self) -> bool:
        return self._highest_acked >= self.config.total_packets

    def window_capacity(self) -> int:
        return max(1, int(self.cwnd))

    def send_next(self) -> None:
        while (
            self._next_packet_id <= self.config.total_packets
            and len(self._in_flight) < self.window_capacity()
        ):
            packet_id = self._next_packet_id
            self._next_packet_id += 1
            self._send_packet(packet_id, is_retransmit=False)

    def on_ack_received(self, ack: Any) -> None:
        ack_id = self._extract_ack_id(ack)
        if ack_id > self._highest_acked:
            self._handle_new_ack(ack_id)
            self._on_new_ack(ack_id)
            self.send_next()
            return

        if ack_id == self._highest_acked and ack_id > 0:
            self._dup_ack_count += 1
            self._on_duplicate_ack(ack_id, self._dup_ack_count)
            self.send_next()

    def on_timeout(self, packet_id: int) -> None:
        if packet_id <= self._highest_acked:
            return
        if packet_id not in self.packet_records:
            return
        self._on_timeout(packet_id)
        self.retransmit_packet(packet_id)

    def retransmit_packet(self, packet_id: int) -> None:
        if packet_id > self.config.total_packets:
            return
        self._send_packet(packet_id, is_retransmit=True)

    def _extract_ack_id(self, ack: Any) -> int:
        if isinstance(ack, int):
            return ack
        if isinstance(ack, dict):
            if "ack_id" in ack:
                return int(ack["ack_id"])
            if "packet_id" in ack:
                return int(ack["packet_id"])
        raise ValueError("ACK must be an int or dict containing ack_id/packet_id")

    def _handle_new_ack(self, ack_id: int) -> None:
        now = self.simulator.get_current_time()
        newly_acked = [pid for pid in self._in_flight if pid <= ack_id]
        for pid in sorted(newly_acked):
            self._in_flight.remove(pid)
            record = self.packet_records.get(pid)
            if record is not None and record.acked_time is None:
                record.acked_time = now
                self.metrics.record_received(pid, now)

        self._highest_acked = ack_id
        self._dup_ack_count = 0

    def _send_packet(self, packet_id: int, is_retransmit: bool) -> None:
        now = self.simulator.get_current_time()
        record = self.packet_records.get(packet_id)
        if record is None:
            record = PacketRecord(
                packet_id=packet_id,
                first_sent_time=now,
                last_sent_time=now,
            )
            self.packet_records[packet_id] = record
        else:
            record.last_sent_time = now
            if is_retransmit:
                record.retransmit_count += 1

        packet = {"packet_id": packet_id}
        self.network.send_packet(packet)
        self.metrics.record_sent(packet_id, now)
        if is_retransmit:
            self.metrics.record_retransmit(packet_id)

        timeout_data = {"packet_id": packet_id}
        self.simulator.schedule_event(
            now + self.config.timeout_interval,
            self.timeout_event_type,
            timeout_data,
        )
        self._in_flight.add(packet_id)

    @staticmethod
    def additive_increase(cwnd: float) -> float:
        return cwnd + (1.0 / max(cwnd, 1.0))

    @abstractmethod
    def _on_new_ack(self, ack_id: int) -> None:
        ...

    @abstractmethod
    def _on_duplicate_ack(self, ack_id: int, dup_ack_count: int) -> None:
        ...

    @abstractmethod
    def _on_timeout(self, packet_id: int) -> None:
        ...
