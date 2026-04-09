from __future__ import annotations

from pathlib import Path

from .models import ExperimentResult


def summarize_results(results: list[ExperimentResult]) -> str:
    if not results:
        return "No experiment results were provided."

    lines = ["TCP Tahoe vs Reno Summary", ""]
    for metric in ("throughput", "goodput", "avg_delay", "jitter"):
        tahoe_values = [getattr(r, metric) for r in results if r.algorithm == "Tahoe"]
        reno_values = [getattr(r, metric) for r in results if r.algorithm == "Reno"]
        if not tahoe_values or not reno_values:
            continue

        tahoe_avg = sum(tahoe_values) / len(tahoe_values)
        reno_avg = sum(reno_values) / len(reno_values)
        if metric in ("throughput", "goodput"):
            winner = "Reno" if reno_avg > tahoe_avg else "Tahoe"
        else:
            winner = "Reno" if reno_avg < tahoe_avg else "Tahoe"

        lines.append(
            f"- {metric}: Tahoe={tahoe_avg:.4f}, Reno={reno_avg:.4f}, better={winner}"
        )

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

    sorted_results = sorted(results, key=lambda item: item.loss_probability)
    metrics = [
        ("throughput", "Throughput (packets/sec)"),
        ("goodput", "Goodput (ratio)"),
        ("avg_delay", "Average Delay"),
        ("jitter", "Delay Jitter"),
    ]

    figure, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    axes_flat = axes.flatten()

    for axis, (metric_key, metric_label) in zip(axes_flat, metrics):
        for algorithm in ("Tahoe", "Reno"):
            algorithm_rows = [r for r in sorted_results if r.algorithm == algorithm]
            x_vals = [r.loss_probability for r in algorithm_rows]
            y_vals = [getattr(r, metric_key) for r in algorithm_rows]
            axis.plot(x_vals, y_vals, marker="o", label=algorithm)

        axis.set_title(metric_label)
        axis.set_xlabel("Loss Probability")
        axis.set_ylabel(metric_label)
        axis.grid(True, alpha=0.3)
        axis.legend()

    figure.suptitle("TCP Tahoe vs Reno Performance", fontsize=14)

    output_file = output_path / "tahoe_vs_reno_metrics.png"
    figure.savefig(output_file)
    plt.close(figure)
    return output_file
