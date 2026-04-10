"""Minimal demo runner using dummy sender/receiver callbacks."""

from simulator.abstractions import BaseReceiver, BaseSender
from simulator.event import EventType
from simulator.metrics import MetricsCollector
from simulator.network import Network, NetworkConfig
from simulator.packet import Ack, Packet
from simulator.simulator import Simulator


class DummySender(BaseSender):
    def __init__(self, simulator: Simulator, total_packets: int = 5) -> None:
        self.simulator = simulator
        self.total_packets = total_packets
        self.next_packet_id = 1

    def bootstrap(self) -> None:
        for _ in range(self.total_packets):
            self.send_next()

    def on_ack_received(self, ack: Ack) -> None:
        # Dummy sender does not adjust window/cwnd; this is just API plumbing.
        _ = ack

    def on_timeout(self, packet_id: int) -> None:
        # Per-packet timer model: timeout triggers retransmission for that packet.
        packet = Packet(packet_id=packet_id)
        self.simulator.schedule_event(
            time=self.simulator.get_current_time(),
            event_type=EventType.SEND,
            data=packet,
        )

    def send_next(self) -> None:
        if self.next_packet_id > self.total_packets:
            return
        packet = Packet(packet_id=self.next_packet_id)
        self.next_packet_id += 1
        self.simulator.schedule_event(
            time=self.simulator.get_current_time(),
            event_type=EventType.SEND,
            data=packet,
        )


class DummyReceiver(BaseReceiver):
    def on_packet_received(self, packet: Packet) -> Ack:
        return Ack(ack_id=packet.packet_id)


def main() -> None:
    total_packets = 8
    propagation_delay = 0.2
    loss_probability = 0.2
    timeout_interval = 0.6

    metrics = MetricsCollector()
    network = Network(NetworkConfig(propagation_delay=propagation_delay, loss_probability=loss_probability), rng_seed=7)
    simulator = Simulator(network=network, metrics=metrics, timeout_interval=timeout_interval)

    sender = DummySender(simulator=simulator, total_packets=total_packets)
    receiver = DummyReceiver()
    simulator.bind_sender(sender)
    simulator.bind_receiver(receiver)

    sender.bootstrap()
    simulator.run()

    total_time = simulator.get_current_time()
    report = metrics.report(total_simulated_time=total_time)

    print("=== Theo Simulator Sanity Metrics ===")
    print(
        f"scenario: packets={total_packets}, loss_probability={loss_probability}, "
        f"one_way_delay={propagation_delay}, timeout_interval={timeout_interval}"
    )
    print(f"simulated_time: {total_time:.3f}s")
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
