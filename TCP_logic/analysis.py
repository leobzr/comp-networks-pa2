from __future__ import annotations

from pathlib import Path

from .models import ExperimentResult


def _algorithm_order(name: str) -> tuple[int, str]:
    preferred = {"Tahoe": 0, "Reno": 1, "Cubic": 2}
    return (preferred.get(name, 100), name)


def _winner(values: dict[str, float], higher_is_better: bool) -> str:
    if higher_is_better:
        best_value = max(values.values())
    else:
        best_value = min(values.values())

    winners = [k for k, v in values.items() if abs(v - best_value) < 1e-9]
    winners.sort(key=_algorithm_order)
    if len(winners) == 1:
        return winners[0]
    return "Tie(" + "/".join(winners) + ")"


def summarize_results(results: list[ExperimentResult]) -> str:
    if not results:
        return "No experiment results were provided."

    algorithms = sorted({r.algorithm for r in results}, key=_algorithm_order)
    if len(algorithms) < 2:
        return "Need at least two algorithms to compare results."

    lines = ["TCP " + " vs ".join(algorithms) + " Summary", ""]

    for metric in ("throughput", "goodput", "avg_delay", "jitter"):
        averages: dict[str, float] = {}
        for algorithm in algorithms:
            values = [getattr(r, metric) for r in results if r.algorithm == algorithm]
            if not values:
                continue
            averages[algorithm] = sum(values) / len(values)

        if len(averages) < 2:
            continue

        higher_is_better = metric in ("throughput", "goodput")
        winner = _winner(averages, higher_is_better=higher_is_better)

        metric_values = ", ".join(
            f"{algorithm}={averages[algorithm]:.4f}" for algorithm in algorithms if algorithm in averages
        )

        lines.append(f"- {metric}: {metric_values}, better={winner}")

    return "\n".join(lines)


def plot_results(results: list[ExperimentResult], output_dir: str = "outputs") -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for graph generation. Install it with pip install matplotlib"
        ) from exc

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    sorted_results = sorted(results, key=lambda item: (item.loss_probability, _algorithm_order(item.algorithm)))
    algorithms = sorted({r.algorithm for r in sorted_results}, key=_algorithm_order)

    metrics = [
        ("throughput", "Throughput (packets/sec)"),
        ("goodput", "Goodput (ratio)"),
        ("avg_delay", "Average Delay"),
        ("jitter", "Delay Jitter"),
    ]

    figure, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    axes_flat = axes.flatten()

    for axis, (metric_key, metric_label) in zip(axes_flat, metrics):
        for algorithm in algorithms:
            algorithm_rows = [r for r in sorted_results if r.algorithm == algorithm]
            x_vals = [r.loss_probability for r in algorithm_rows]
            y_vals = [getattr(r, metric_key) for r in algorithm_rows]
            axis.plot(x_vals, y_vals, marker="o", label=algorithm)

        axis.set_title(metric_label)
        axis.set_xlabel("Loss Probability")
        axis.set_ylabel(metric_label)
        axis.grid(True, alpha=0.3)
        axis.legend()

    figure.suptitle("TCP Congestion Control Performance", fontsize=14)

    output_file = output_path / "tcp_cc_metrics.png"
    figure.savefig(output_file)
    plt.close(figure)
    return output_file
