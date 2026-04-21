import unittest

from TCP_logic.config import SenderConfig
from TCP_logic.cubic import TCPCubic
from tests.fakes import FakeMetrics, FakeNetwork, FakeSimulator


class CubicTests(unittest.TestCase):
    def test_congestion_avoidance_growth_after_slow_start(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=20, initial_cwnd=1.0, initial_ssthresh=2.0)
        sender = TCPCubic(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)  # slow start: cwnd 1 -> 2
        cwnd_before_ca_ack = sender.cwnd

        sender.on_ack_received(2)  # congestion avoidance under CUBIC logic

        self.assertGreater(sender.cwnd, cwnd_before_ca_ack)

    def test_triple_duplicate_ack_applies_multiplicative_decrease(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=30, initial_cwnd=8.0, initial_ssthresh=32.0)
        sender = TCPCubic(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)

        sender.on_ack_received(1)
        sender.on_ack_received(1)
        sender.on_ack_received(1)

        self.assertAlmostEqual(sender.cwnd, sender.ssthresh)
        self.assertIn(2, metrics.retransmitted_ids)

    def test_timeout_resets_to_initial_cwnd(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=10, initial_cwnd=2.0, initial_ssthresh=16.0)
        sender = TCPCubic(simulator, network, metrics, config)

        sender.send_next()
        sender.on_timeout(1)

        self.assertEqual(sender.cwnd, config.initial_cwnd)
        self.assertGreaterEqual(sender.ssthresh, 2.0)
        self.assertIn(1, metrics.retransmitted_ids)

    def test_stale_timeout_ignored_after_ack(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=10, initial_cwnd=1.0, initial_ssthresh=16.0)
        sender = TCPCubic(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)

        retransmits_before = len(metrics.retransmitted_ids)
        cwnd_before = sender.cwnd
        sender.on_timeout(1)

        self.assertEqual(len(metrics.retransmitted_ids), retransmits_before)
        self.assertEqual(sender.cwnd, cwnd_before)


if __name__ == "__main__":
    unittest.main()
