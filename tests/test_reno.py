import unittest

from TCP_logic.config import SenderConfig
from TCP_logic.reno import TCPReno
from tests.fakes import FakeMetrics, FakeNetwork, FakeSimulator


class RenoTests(unittest.TestCase):
    def test_triple_duplicate_ack_enters_fast_recovery(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=20, initial_cwnd=6.0, initial_ssthresh=32.0)
        sender = TCPReno(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)

        sender.on_ack_received(1)
        sender.on_ack_received(1)
        sender.on_ack_received(1)

        self.assertTrue(sender.in_fast_recovery)
        self.assertIn(2, metrics.retransmitted_ids)
        self.assertAlmostEqual(sender.ssthresh, 3.5)
        self.assertAlmostEqual(sender.cwnd, sender.ssthresh + config.dup_ack_threshold)

    def test_new_ack_exits_fast_recovery(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=20, initial_cwnd=6.0, initial_ssthresh=32.0)
        sender = TCPReno(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)
        sender.on_ack_received(1)
        sender.on_ack_received(1)
        sender.on_ack_received(1)

        recovery_point = sender.recovery_ack_point
        sender.on_ack_received(recovery_point)

        self.assertFalse(sender.in_fast_recovery)
        self.assertAlmostEqual(sender.cwnd, sender.ssthresh)

    def test_timeout_exits_fast_recovery(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=20, initial_cwnd=6.0, initial_ssthresh=32.0)
        sender = TCPReno(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)
        sender.on_ack_received(1)
        sender.on_ack_received(1)
        sender.on_ack_received(1)

        sender.on_timeout(2)

        self.assertFalse(sender.in_fast_recovery)
        self.assertEqual(sender.cwnd, config.initial_cwnd)
        self.assertIn(2, metrics.retransmitted_ids)

    def test_stale_timeout_ignored_after_ack(self) -> None:
        simulator = FakeSimulator()
        network = FakeNetwork()
        metrics = FakeMetrics()
        config = SenderConfig(total_packets=20, initial_cwnd=1.0, initial_ssthresh=16.0)
        sender = TCPReno(simulator, network, metrics, config)

        sender.send_next()
        sender.on_ack_received(1)

        retransmits_before = len(metrics.retransmitted_ids)
        cwnd_before = sender.cwnd
        sender.on_timeout(1)

        self.assertEqual(len(metrics.retransmitted_ids), retransmits_before)
        self.assertEqual(sender.cwnd, cwnd_before)


if __name__ == "__main__":
    unittest.main()
