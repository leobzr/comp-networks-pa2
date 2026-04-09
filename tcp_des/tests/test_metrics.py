from simulator.metrics import MetricsCollector


def test_metrics_report_basic_values():
    metrics = MetricsCollector()

    metrics.record_sent(packet_id=1, time=0.0)
    metrics.record_sent(packet_id=2, time=1.0)
    metrics.record_received(packet_id=1, time=0.5)
    metrics.record_received(packet_id=2, time=1.8)

    report = metrics.report(total_simulated_time=2.0)

    assert report["throughput"] == 1.0
    assert report["goodput"] == 1.0
    assert report["average_delay"] == 0.65
    assert report["unique_packets_delivered"] == 2


def test_metrics_retransmission_counts_against_total_packets_sent():
    metrics = MetricsCollector()

    metrics.record_sent(packet_id=1, time=0.0)
    metrics.record_sent(packet_id=1, time=1.0)
    metrics.record_sent(packet_id=1, time=2.0)
    metrics.record_received(packet_id=1, time=2.5)

    report = metrics.report(total_simulated_time=3.0)

    assert report["total_packets_sent"] == 3
    assert report["unique_packets_delivered"] == 1
    assert report["goodput"] == (1 / 3)
    assert report["delay_jitter"] == 0.0
