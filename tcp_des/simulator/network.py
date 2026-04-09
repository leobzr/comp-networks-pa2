"""Network model with fixed delay and random drop probability."""

import random
from dataclasses import dataclass

from .event import EventType
from .packet import Ack, Packet


@dataclass
class NetworkConfig:
    # Fixed one-way propagation delay. RTT is 2 * propagation_delay.
    propagation_delay: float = 0.1
    # Loss applies to data packets only (not ACKs) for deterministic testing.
    loss_probability: float = 0.0


class Network:
    def __init__(self, config: NetworkConfig, rng_seed: int | None = None) -> None:
        self.config = config
        self._rng = random.Random(rng_seed)

    def should_drop(self) -> bool:
        # Independent Bernoulli loss per data packet arrival.
        return self._rng.random() < self.config.loss_probability

    def send_packet(self, packet: Packet, now: float, schedule_event) -> None:
        # Data packet arrives one-way delay later unless dropped.
        arrival_time = now + self.config.propagation_delay
        if self.should_drop():
            schedule_event(arrival_time, EventType.DROP, data=packet)
            return
        schedule_event(arrival_time, EventType.RECEIVE, data=packet)

    def send_ack(self, ack: Ack, now: float, schedule_event) -> None:
        # ACK path is reliable in this simplified model.
        arrival_time = now + self.config.propagation_delay
        schedule_event(arrival_time, EventType.ACK, data=ack)
