from dataclasses import dataclass


@dataclass(slots=True)
class PacketRecord:
    packet_id: int
    first_sent_time: float
    last_sent_time: float
    retransmit_count: int = 0
    acked_time: float | None = None


@dataclass(slots=True)
class ExperimentResult:
    algorithm: str
    loss_probability: float
    throughput: float
    goodput: float
    avg_delay: float
    jitter: float
    seed: int
    completed: bool
