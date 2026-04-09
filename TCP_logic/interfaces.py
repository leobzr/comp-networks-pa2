from typing import Any, Protocol


class SimulatorLike(Protocol):
    def schedule_event(self, time: float, event_type: str, data: Any) -> None:
        ...

    def get_current_time(self) -> float:
        ...

    def run(self) -> None:
        ...


class NetworkLike(Protocol):
    def send_packet(self, packet: dict[str, Any]) -> None:
        ...


class MetricsCollectorLike(Protocol):
    def record_sent(self, packet_id: int, time: float) -> None:
        ...

    def record_received(self, packet_id: int, time: float) -> None:
        ...

    def record_dropped(self, packet_id: int) -> None:
        ...

    def record_retransmit(self, packet_id: int) -> None:
        ...

    def report(self) -> dict[str, float]:
        ...
