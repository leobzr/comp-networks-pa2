from tcp_des.simulator.event import EventType
from tcp_des.simulator.network import Network, NetworkConfig
from tcp_des.simulator.packet import Ack, Packet


def test_network_drop_probability_zero_never_drops():
    network = Network(NetworkConfig(loss_probability=0.0), rng_seed=1)
    events = []
    for packet_id in range(20):
        network.send_packet(
            packet=Packet(packet_id=packet_id),
            now=0.0,
            schedule_event=lambda time, event_type, data, priority=0: events.append(event_type),
        )

    assert all(event_type == EventType.RECEIVE for event_type in events)


def test_network_drop_probability_one_always_drops():
    network = Network(NetworkConfig(loss_probability=1.0), rng_seed=1)
    events = []
    for packet_id in range(20):
        network.send_packet(
            packet=Packet(packet_id=packet_id),
            now=0.0,
            schedule_event=lambda time, event_type, data, priority=0: events.append(event_type),
        )

    assert all(event_type == EventType.DROP for event_type in events)


def test_acks_are_not_dropped_even_with_full_loss_probability():
    network = Network(NetworkConfig(loss_probability=1.0), rng_seed=1)
    events = []
    for packet_id in range(10):
        network.send_ack(
            ack=Ack(ack_id=packet_id),
            now=0.0,
            schedule_event=lambda time, event_type, data, priority=0: events.append(event_type),
        )

    assert all(event_type == EventType.ACK for event_type in events)
