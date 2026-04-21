from __future__ import annotations

from .config import SenderConfig
from .interfaces import MetricsCollectorLike, NetworkLike, SimulatorLike
from .sender import TCPSender


class TCPCubic(TCPSender):
    """RFC 9438-inspired CUBIC sender for the PA2 DES model.

    This implementation keeps the simulator interface consistent with Tahoe/Reno
    while modeling CUBIC's key behaviors:
    - Cubic window growth during congestion avoidance.
    - Reno-friendly fallback through West.
    - Multiplicative decrease with beta=0.7 on congestion events.
    """

    beta_cubic = 0.7
    cubic_c = 0.4

    def __init__(
        self,
        simulator: SimulatorLike,
        network: NetworkLike,
        metrics: MetricsCollectorLike,
        config: SenderConfig,
    ) -> None:
        super().__init__(simulator, network, metrics, config, name="Cubic")

        # CUBIC state variables from RFC 9438 terminology.
        self.w_max = self.cwnd
        self.cwnd_prior = self.cwnd
        self.epoch_start: float | None = None
        self.cwnd_epoch = self.cwnd
        self.k = 0.0
        self.w_est = self.cwnd

        self.alpha_base = 3.0 * (1.0 - self.beta_cubic) / (1.0 + self.beta_cubic)
        self.alpha_cubic = self.alpha_base

        # Single-flow experiments generally do better with fast convergence off.
        self.fast_convergence = False

        # Start with a practical RTT estimate and refine on each new ACK.
        self.smoothed_rtt = max(0.001, self.config.timeout_interval / 2.0)

    def _on_new_ack(self, ack_id: int) -> None:
        self._update_smoothed_rtt(ack_id)

        if self.cwnd < self.ssthresh:
            self.cwnd += 1.0
            return

        self._ensure_epoch()
        now = self.simulator.get_current_time()
        t_elapsed = max(0.0, now - (self.epoch_start or now))

        target = self._target_window_after_rtt(t_elapsed)
        self._update_west()

        if target < self.w_est:
            self.cwnd = max(self.cwnd, self.w_est)
            return

        self._increase_towards_target(target)

    def _on_duplicate_ack(self, ack_id: int, dup_ack_count: int) -> None:
        if dup_ack_count != self.config.dup_ack_threshold:
            return

        self._on_congestion_event(reset_to_initial=False)
        self.retransmit_packet(ack_id + 1)

    def _on_timeout(self, packet_id: int) -> None:
        self._on_congestion_event(reset_to_initial=True)

    def _update_smoothed_rtt(self, ack_id: int) -> None:
        now = self.simulator.get_current_time()
        record = self.packet_records.get(ack_id)
        if record is None:
            return

        sample_rtt = now - record.last_sent_time
        if sample_rtt <= 0:
            return

        self.smoothed_rtt = 0.875 * self.smoothed_rtt + 0.125 * sample_rtt

    def _ensure_epoch(self) -> None:
        if self.epoch_start is not None:
            return

        self.epoch_start = self.simulator.get_current_time()
        self.cwnd_epoch = self.cwnd
        self.w_est = self.cwnd_epoch
        self.alpha_cubic = self.alpha_base

        if self.w_max <= self.cwnd_epoch:
            self.k = 0.0
        else:
            self.k = ((self.w_max - self.cwnd_epoch) / self.cubic_c) ** (1.0 / 3.0)

    def _target_window_after_rtt(self, t_elapsed: float) -> float:
        t_with_rtt = t_elapsed + self.smoothed_rtt
        return self.cubic_c * ((t_with_rtt - self.k) ** 3) + self.w_max

    def _update_west(self) -> None:
        self.w_est += self.alpha_cubic / max(self.cwnd, 1.0)
        if self.w_est >= self.cwnd_prior:
            self.alpha_cubic = 1.0

    def _increase_towards_target(self, target: float) -> None:
        target = max(target, self.cwnd)
        additive_floor = 1.0 / max(self.cwnd, 1.0)
        growth = (target - self.cwnd) / max(self.cwnd, 1.0)

        growth = max(growth, additive_floor)
        growth = min(growth, 1.0)
        self.cwnd += growth

    def _on_congestion_event(self, reset_to_initial: bool) -> None:
        self.cwnd_prior = self.cwnd

        if self.fast_convergence and self.cwnd < self.w_max:
            self.w_max = (self.cwnd * (1.0 + self.beta_cubic)) / 2.0
        else:
            self.w_max = self.cwnd

        flight_size = max(float(len(self.in_flight)), 1.0)
        self.ssthresh = max(self.beta_cubic * flight_size, 2.0)

        if reset_to_initial:
            self.cwnd = float(self.config.initial_cwnd)
        else:
            self.cwnd = self.ssthresh

        self.epoch_start = None
        self.k = 0.0
        self.w_est = self.cwnd
        self.alpha_cubic = self.alpha_base
        self._dup_ack_count = 0
