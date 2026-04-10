from __future__ import annotations

from tcp_des.simulator.abstractions import BaseReceiver, BaseSender
from tcp_des.simulator.event import EventType
from tcp_des.simulator.metrics import MetricsCollector
from tcp_des.simulator.network import Network, NetworkConfig
from tcp_des.simulator.packet import Ack, Packet
from tcp_des.simulator.simulator import Simulator

from .config import SenderConfig
from .experiment import SimulationStack


class CumulativeAckReceiver(BaseReceiver):
    """Simple receiver that ACKs each packet id cumulatively by id."""

    def on_packet_received(self, packet: Packet) -> Ack:
        return Ack(ack_id=packet.packet_id)


class GapAwareCumulativeAckReceiver(BaseReceiver):
    """ACKs highest contiguous packet id; emits duplicate ACKs when gaps exist."""

    def __init__(self) -> None:
        self._received: set[int] = set()
        self._highest_contiguous = 0

    def on_packet_received(self, packet: Packet) -> Ack:
        self._received.add(packet.packet_id)
        while (self._highest_contiguous + 1) in self._received:
            self._highest_contiguous += 1
        return Ack(ack_id=self._highest_contiguous)


class SenderBridge(BaseSender):
    """Bridge simulator callbacks into Leo sender callbacks."""

    def __init__(self, sender) -> None:
        self._sender = sender

    def on_ack_received(self, ack: Ack) -> None:
        self._sender.on_ack_received({"ack_id": ack.ack_id})

    def on_timeout(self, packet_id: int) -> None:
        self._sender.on_timeout(packet_id)

    def send_next(self) -> None:
        self._sender.send_next()


class SimulatorAdapter:
    """Adapts Leo schedule_event shape to simulator EventType events."""

    def __init__(self, simulator: Simulator) -> None:
        self._simulator = simulator

    def schedule_event(self, time: float, event_type, data=None) -> None:
        mapped_event_type = event_type
        if isinstance(event_type, str):
            normalized = event_type.upper()
            if normalized == "TIMEOUT":
                mapped_event_type = EventType.TIMEOUT
            elif normalized in EventType.__members__:
                mapped_event_type = EventType[normalized]
            else:
                raise ValueError(f"Unsupported event type string: {event_type}")

        mapped_data = data
        if mapped_event_type == EventType.TIMEOUT and isinstance(data, dict):
            mapped_data = int(data["packet_id"])

        self._simulator.schedule_event(time=time, event_type=mapped_event_type, data=mapped_data)

    def get_current_time(self) -> float:
        return self._simulator.get_current_time()

    def run(self) -> None:
        self._simulator.run()


class NetworkAdapter:
    """Adapts sender packet dicts to simulator Packet events through network model."""

    def __init__(self, network: Network, simulator: Simulator) -> None:
        self._network = network
        self._simulator = simulator

    def send_packet(self, packet: dict[str, int]) -> None:
        wrapped = Packet(packet_id=int(packet["packet_id"]))
        now = self._simulator.get_current_time()
        self._network.send_packet(packet=wrapped, now=now, schedule_event=self._simulator.schedule_event)


class MetricsAdapter:
    """Adapts simulator metric names/signature to Leo expectations."""

    def __init__(self, metrics: MetricsCollector, simulator: Simulator) -> None:
        self._metrics = metrics
        self._simulator = simulator

    def record_sent(self, packet_id: int, time: float) -> None:
        self._metrics.record_sent(packet_id, time)

    def record_received(self, packet_id: int, time: float) -> None:
        # Simulator already records ACK delivery in _handle_ack.
        return None

    def record_dropped(self, packet_id: int) -> None:
        self._metrics.record_dropped(packet_id)

    def record_retransmit(self, packet_id: int) -> None:
        self._metrics.record_retransmit(packet_id)

    def report(self) -> dict[str, float]:
        raw = self._metrics.report(total_simulated_time=self._simulator.get_current_time())
        return {
            "throughput": float(raw.get("throughput", 0.0)),
            "goodput": float(raw.get("goodput", 0.0)),
            "avg_delay": float(raw.get("average_delay", 0.0)),
            "jitter": float(raw.get("delay_jitter", 0.0)),
        }


def create_integrated_stack(
    loss_probability: float,
    seed: int,
    config: SenderConfig,
    propagation_delay: float = 0.1,
    receiver_mode: str = "simple",
) -> SimulationStack:
    """Create one integrated simulator stack for a loss probability point."""
    metrics = MetricsCollector()
    network = Network(
        NetworkConfig(propagation_delay=propagation_delay, loss_probability=loss_probability),
        rng_seed=seed,
    )
    simulator = Simulator(network=network, metrics=metrics, timeout_interval=config.timeout_interval)
    if receiver_mode == "simple":
        simulator.bind_receiver(CumulativeAckReceiver())
    elif receiver_mode == "gap-aware":
        simulator.bind_receiver(GapAwareCumulativeAckReceiver())
    else:
        raise ValueError(f"Unsupported receiver_mode: {receiver_mode}")

    sim_adapter = SimulatorAdapter(simulator)
    net_adapter = NetworkAdapter(network=network, simulator=simulator)
    metrics_adapter = MetricsAdapter(metrics=metrics, simulator=simulator)

    def _bind(sender: object) -> None:
        simulator.bind_sender(SenderBridge(sender))

    return SimulationStack(
        simulator=sim_adapter,
        network=net_adapter,
        metrics=metrics_adapter,
        bind_sender=_bind,
    )
