from __future__ import annotations

from .analysis import plot_results, summarize_results
from .config import SenderConfig
from .experiment import run_loss_sweep
from .integration import create_integrated_stack


def build_loss_sweep(start: float = 0.0, end: float = 0.06, step: float = 0.01) -> list[float]:
    values: list[float] = []
    current = start
    while current <= end + 1e-12:
        values.append(round(current, 6))
        current += step
    return values


def main() -> None:
    # Long-distance scenario with higher propagation delay (RTT ~ 0.6s).
    config = SenderConfig(
        total_packets=600,
        timeout_interval=2.0,
        initial_cwnd=6.0,
        initial_ssthresh=24.0,
        dup_ack_threshold=3,
    )
    loss_probabilities = build_loss_sweep()

    print("LONG-DISTANCE SCENARIO CHANGES (vs baseline):")
    print("- receiver_mode: gap-aware cumulative ACK")
    print("- propagation_delay: 0.3s (RTT ~ 0.6s)")
    print(f"- total_packets: {config.total_packets}")
    print(f"- timeout_interval: {config.timeout_interval}")
    print(f"- initial_cwnd: {config.initial_cwnd}")
    print(f"- initial_ssthresh: {config.initial_ssthresh}")
    print(
        f"- loss_sweep: start={loss_probabilities[0]}, end={loss_probabilities[-1]}, "
        f"step={loss_probabilities[1] - loss_probabilities[0]}"
    )

    def simulation_factory(loss_probability: float, seed: int):
        return create_integrated_stack(
            loss_probability=loss_probability,
            seed=seed,
            config=config,
            propagation_delay=0.3,
            receiver_mode="gap-aware",
        )

    results = run_loss_sweep(
        loss_probabilities=loss_probabilities,
        base_seed=29,
        config=config,
        simulation_factory=simulation_factory,
    )

    print("\nLONG-DISTANCE RESULTS")
    print(summarize_results(results))
    plot_path = plot_results(results, output_dir="outputs/long_distance")
    print(f"Saved plot to: {plot_path}")


if __name__ == "__main__":
    main()
