from __future__ import annotations

from .analysis import plot_results, summarize_results
from .config import SenderConfig
from .experiment import run_loss_sweep
from .integration import create_integrated_stack


def build_loss_sweep(start: float = 0.0, end: float = 0.1, step: float = 0.01) -> list[float]:
    values: list[float] = []
    current = start
    while current <= end + 1e-12:
        values.append(round(current, 6))
        current += step
    return values


def main() -> None:
    config = SenderConfig()
    loss_probabilities = build_loss_sweep()

    def simulation_factory(loss_probability: float, seed: int):
        return create_integrated_stack(
            loss_probability=loss_probability,
            seed=seed,
            config=config,
        )

    results = run_loss_sweep(
        loss_probabilities=loss_probabilities,
        base_seed=7,
        config=config,
        simulation_factory=simulation_factory,
    )

    print(summarize_results(results))
    plot_path = plot_results(results)
    print(f"Saved plot to: {plot_path}")


if __name__ == "__main__":
    main()
