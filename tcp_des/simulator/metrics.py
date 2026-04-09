"""Metrics collection for throughput, goodput, delay, and jitter."""

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass
class PacketTiming:
    time_first_sent: float | None = None
    time_acked: float | None = None
    retransmit_count: int = 0


class MetricsCollector:
    def __init__(self) -> None:
        self.total_packets_sent = 0
        self.total_packets_dropped = 0
        self._packet_data = defaultdict(PacketTiming)

    def record_sent(self, packet_id: int, time: float) -> None:
        # First send sets delay baseline; retransmit count is tracked by record_retransmit.
        self.total_packets_sent += 1
        entry = self._packet_data[packet_id]
        if entry.time_first_sent is None:
            entry.time_first_sent = time

    def record_received(self, packet_id: int, time: float) -> None:
        self._packet_data[packet_id].time_acked = time

    def record_dropped(self, packet_id: int) -> None:
        self.total_packets_dropped += 1

    def record_retransmit(self, packet_id: int) -> None:
        self._packet_data[packet_id].retransmit_count += 1

    def report(self, total_simulated_time: float) -> dict:
        # Only packets with both first-send and ACK timestamps are considered delivered.
        delivered = [p for p in self._packet_data.values() if p.time_acked is not None and p.time_first_sent is not None]
        unique_delivered = len(delivered)

        delays = [p.time_acked - p.time_first_sent for p in delivered]

        # Population stdev is used for jitter to keep the metric stable for small runs.
        throughput = (unique_delivered / total_simulated_time) if total_simulated_time > 0 else 0.0
        goodput = (unique_delivered / self.total_packets_sent) if self.total_packets_sent > 0 else 0.0
        avg_delay = mean(delays) if delays else 0.0
        jitter = pstdev(delays) if len(delays) > 1 else 0.0

        return {
            "throughput": throughput,
            "goodput": goodput,
            "average_delay": avg_delay,
            "delay_jitter": jitter,
            "total_packets_sent": self.total_packets_sent,
            "unique_packets_delivered": unique_delivered,
            "total_packets_dropped": self.total_packets_dropped,
        }
