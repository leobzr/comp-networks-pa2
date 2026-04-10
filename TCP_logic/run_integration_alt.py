from __future__ import annotations

from .analysis import plot_results, summarize_results
from .config import SenderConfig
from .experiment import run_loss_sweep
from .integration import create_integrated_stack


def build_loss_sweep(start: float = 0.02, end: float = 0.20, step: float = 0.02) -> list[float]:
    values: list[float] = []
    current = start
    while current <= end + 1e-12:
        values.append(round(current, 6))
        current += step
    return values


def main() -> None:
    # Alternate scenario tuned to expose Reno fast recovery behavior more clearly.
    config = SenderConfig(
        total_packets=400,
        timeout_interval=0.9,
        initial_cwnd=6.0,
        initial_ssthresh=24.0,
        dup_ack_threshold=3,
    )
    loss_probabilities = build_loss_sweep()

    print("ALT SCENARIO CHANGES (vs baseline):")
    print("- receiver_mode: gap-aware cumulative ACK (duplicate ACKs can occur on out-of-order arrival)")
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
            propagation_delay=0.1,
            receiver_mode="gap-aware",
        )

    results = run_loss_sweep(
        loss_probabilities=loss_probabilities,
        base_seed=17,
        config=config,
        simulation_factory=simulation_factory,
    )

    print("\nALT SCENARIO RESULTS: gap-aware cumulative ACK receiver")
    print(summarize_results(results))
    plot_path = plot_results(results, output_dir="outputs/alt_scenario")
    print(f"Saved plot to: {plot_path}")


if __name__ == "__main__":
    main()
