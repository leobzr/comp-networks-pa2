from dataclasses import dataclass


@dataclass(slots=True)
class SenderConfig:

    total_packets: int = 1000
    timeout_interval: float = 1.0
    initial_cwnd: float = 1.0
    initial_ssthresh: float = 16.0
    dup_ack_threshold: int = 3

    def __post_init__(self) -> None:
        if self.total_packets <= 0:
            raise ValueError("total_packets must be positive")
        if self.timeout_interval <= 0:
            raise ValueError("timeout_interval must be positive")
        if self.initial_cwnd <= 0:
            raise ValueError("initial_cwnd must be positive")
        if self.initial_ssthresh <= 0:
            raise ValueError("initial_ssthresh must be positive")
        if self.dup_ack_threshold <= 0:
            raise ValueError("dup_ack_threshold must be positive")
