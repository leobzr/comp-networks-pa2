from .config import SenderConfig
from .interfaces import MetricsCollectorLike, NetworkLike, SimulatorLike
from .sender import TCPSender


class TCPTahoe(TCPSender):
    def __init__(
        self,
        simulator: SimulatorLike,
        network: NetworkLike,
        metrics: MetricsCollectorLike,
        config: SenderConfig,
    ) -> None:
        super().__init__(simulator, network, metrics, config, name="Tahoe")

    def _on_new_ack(self, ack_id: int) -> None:
        if self.cwnd < self.ssthresh:
            self.cwnd += 1.0
        else:
            self.cwnd = self.additive_increase(self.cwnd)

    def _on_duplicate_ack(self, ack_id: int, dup_ack_count: int) -> None:
        if dup_ack_count != self.config.dup_ack_threshold:
            return

        self.ssthresh = max(self.cwnd / 2.0, 2.0)
        self.cwnd = float(self.config.initial_cwnd)
        self._dup_ack_count = 0

        lost_packet_id = ack_id + 1
        self.retransmit_packet(lost_packet_id)

    def _on_timeout(self, packet_id: int) -> None:
        self.ssthresh = max(self.cwnd / 2.0, 2.0)
        self.cwnd = float(self.config.initial_cwnd)
        self._dup_ack_count = 0
