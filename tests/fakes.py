from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt


@dataclass
class FakeSimulator:
    now: float = 0.0
    scheduled: list[tuple[float, str, dict[str, int]]] = field(default_factory=list)

    def schedule_event(self, time: float, event_type: str, data: dict[str, int]) -> None:
        self.scheduled.append((time, event_type, data))

    def get_current_time(self) -> float:
        return self.now

    def run(self) -> None:
        return None


@dataclass
class FakeNetwork:
    sent_packets: list[dict[str, int]] = field(default_factory=list)

    def send_packet(self, packet: dict[str, int]) -> None:
        self.sent_packets.append(packet)


@dataclass
class FakeMetrics:
    sent_ids: list[int] = field(default_factory=list)
    received_ids: list[int] = field(default_factory=list)
    retransmitted_ids: list[int] = field(default_factory=list)

    def record_sent(self, packet_id: int, time: float) -> None:
        self.sent_ids.append(packet_id)

    def record_received(self, packet_id: int, time: float) -> None:
        self.received_ids.append(packet_id)

    def record_dropped(self, packet_id: int) -> None:
        return None

    def record_retransmit(self, packet_id: int) -> None:
        self.retransmitted_ids.append(packet_id)

    def report(self) -> dict[str, float]:
        total_sent = len(self.sent_ids)
        unique_received = len(set(self.received_ids))
        delays = [1.0 for _ in self.received_ids]
        avg_delay = (sum(delays) / len(delays)) if delays else 0.0
        if delays:
            mean = avg_delay
            variance = sum((d - mean) ** 2 for d in delays) / len(delays)
            jitter = sqrt(variance)
        else:
            jitter = 0.0

        return {
            "throughput": float(unique_received),
            "goodput": (unique_received / total_sent) if total_sent else 0.0,
            "avg_delay": avg_delay,
            "jitter": jitter,
        }
