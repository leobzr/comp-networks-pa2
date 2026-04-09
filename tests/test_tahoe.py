import unittest

from TCP_logic.config import SenderConfig
from TCP_logic.tahoe import TCPTahoe
from tests.fakes import FakeMetrics, FakeNetwork, FakeSimulator


class TahoeTests(unittest.TestCase):
    def test_slow_start_growth_after_ack(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=10, initial_cwnd=1.0, initial_ssthresh=16.0)
        sender = TCPTahoe(simulator, network, metrics, config)

        sender.send_next()
        self.assertEqual(len(network.sent_packets), 1)

        sender.on_ack_received(1)

        self.assertEqual(sender.highest_acked, 1)
        self.assertEqual(sender.cwnd, 2.0)
        self.assertEqual(len(network.sent_packets), 3)

    def test_triple_duplicate_ack_triggers_tahoe_reset(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=20, initial_cwnd=4.0, initial_ssthresh=20.0)
        sender = TCPTahoe(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)

        sender.on_ack_received(1)
        sender.on_ack_received(1)
        sender.on_ack_received(1)

        self.assertEqual(sender.cwnd, config.initial_cwnd)
        self.assertIn(2, metrics.retransmitted_ids)

    def test_timeout_resets_cwnd_and_halves_ssthresh(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=10, initial_cwnd=8.0, initial_ssthresh=32.0)
        sender = TCPTahoe(simulator, network, metrics, config)

        sender.send_next()
        sender.on_timeout(1)

        self.assertEqual(sender.cwnd, config.initial_cwnd)
        self.assertAlmostEqual(sender.ssthresh, 4.0)
        self.assertIn(1, metrics.retransmitted_ids)

    def test_stale_timeout_ignored_after_ack(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=10, initial_cwnd=1.0, initial_ssthresh=16.0)
        sender = TCPTahoe(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)

        retransmits_before = len(metrics.retransmitted_ids)
        cwnd_before = sender.cwnd
        sender.on_timeout(1)

        self.assertEqual(len(metrics.retransmitted_ids), retransmits_before)
        self.assertEqual(sender.cwnd, cwnd_before)


if __name__ == "__main__":
    unittest.main()
