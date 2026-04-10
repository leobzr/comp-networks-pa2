from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .config import SenderConfig
from .interfaces import MetricsCollectorLike, NetworkLike, SimulatorLike
from .models import ExperimentResult
from .reno import TCPReno
from .tahoe import TCPTahoe


@dataclass(slots=True)
class SimulationStack:
    simulator: SimulatorLike
    network: NetworkLike
    metrics: MetricsCollectorLike
    bind_sender: Callable[[object], None] | None = None


SimulationFactory = Callable[[float, int], SimulationStack]


def run_single_experiment(
    algorithm: str,
    loss_probability: float,
    seed: int,
    config: SenderConfig,
    simulation_factory: SimulationFactory,
) -> ExperimentResult:
    """Run one Tahoe/Reno experiment against Theo simulator APIs.

    Expected integration assumptions from the shared project contract:
    - Loss is applied to data packets only.
    - ACKs are never dropped.
    - Per-packet timeout events may fire after ACK; sender ignores stale timeouts.
    """
    stack = simulation_factory(loss_probability, seed)

    if algorithm == "Tahoe":
        sender = TCPTahoe(stack.simulator, stack.network, stack.metrics, config)
    elif algorithm == "Reno":
        sender = TCPReno(stack.simulator, stack.network, stack.metrics, config)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    if stack.bind_sender is not None:
        stack.bind_sender(sender)
    elif hasattr(stack.simulator, "bind_sender"):
        stack.simulator.bind_sender(sender)

    sender.send_next()
    stack.simulator.run()

    report = stack.metrics.report()
    return ExperimentResult(
        algorithm=algorithm,
        loss_probability=loss_probability,
        throughput=float(report.get("throughput", 0.0)),
        goodput=float(report.get("goodput", 0.0)),
        avg_delay=float(report.get("avg_delay", 0.0)),
        jitter=float(report.get("jitter", 0.0)),
        seed=seed,
        completed=sender.is_complete(),
    )


def run_loss_sweep(
    loss_probabilities: Iterable[float],
    base_seed: int,
    config: SenderConfig,
    simulation_factory: SimulationFactory,
) -> list[ExperimentResult]:
    results: list[ExperimentResult] = []

    for loss_probability in loss_probabilities:
        run_seed = base_seed + int(loss_probability * 10_000)
        for algorithm in ("Tahoe", "Reno"):
            result = run_single_experiment(
                algorithm=algorithm,
                loss_probability=loss_probability,
                seed=run_seed,
                config=config,
                simulation_factory=simulation_factory,
            )
            results.append(result)

    return results


def results_as_rows(results: list[ExperimentResult]) -> list[dict[str, float | int | str | bool]]:
    rows: list[dict[str, float | int | str | bool]] = []
    for result in results:
        rows.append(
            {
                "algorithm": result.algorithm,
                "loss_probability": result.loss_probability,
                "throughput": result.throughput,
                "goodput": result.goodput,
                "avg_delay": result.avg_delay,
                "jitter": result.jitter,
                "seed": result.seed,
                "completed": result.completed,
            }
        )
    return rows
