from .config import SenderConfig
from .interfaces import MetricsCollectorLike, NetworkLike, SimulatorLike
from .sender import TCPSender


class TCPReno(TCPSender):
    def __init__(
        self,
        simulator: SimulatorLike,
        network: NetworkLike,
        metrics: MetricsCollectorLike,
        config: SenderConfig,
    ) -> None:
        super().__init__(simulator, network, metrics, config, name="Reno")
        self.in_fast_recovery = False
        self.recovery_ack_point = 0

    def _on_new_ack(self, ack_id: int) -> None:
        if self.in_fast_recovery:
            if ack_id >= self.recovery_ack_point:
                self.in_fast_recovery = False
                self.cwnd = self.ssthresh
            else:
                self.cwnd = self.ssthresh + float(self.config.dup_ack_threshold)
                self.retransmit_packet(ack_id + 1)
            return

        if self.cwnd < self.ssthresh:
            self.cwnd += 1.0
        else:
            self.cwnd = self.additive_increase(self.cwnd)

    def _on_duplicate_ack(self, ack_id: int, dup_ack_count: int) -> None:
        if not self.in_fast_recovery and dup_ack_count == self.config.dup_ack_threshold:
            self.ssthresh = max(self.cwnd / 2.0, 2.0)
            self.cwnd = self.ssthresh + float(self.config.dup_ack_threshold)
            self.in_fast_recovery = True
            self.recovery_ack_point = max(self.in_flight) if self.in_flight else ack_id
            self.retransmit_packet(ack_id + 1)
            return

        if self.in_fast_recovery and dup_ack_count > self.config.dup_ack_threshold:
            self.cwnd += 1.0

    def _on_timeout(self, packet_id: int) -> None:
        self.ssthresh = max(self.cwnd / 2.0, 2.0)
        self.cwnd = float(self.config.initial_cwnd)
        self.in_fast_recovery = False
        self.recovery_ack_point = 0
        self._dup_ack_count = 0
