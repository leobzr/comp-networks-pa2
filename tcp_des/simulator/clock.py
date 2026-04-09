"""Simulated clock utilities."""


class SimulatedClock:
    """Tracks simulation time without using wall-clock time."""

    def __init__(self) -> None:
        self._time = 0.0

    def now(self) -> float:
        return self._time

    def advance_to(self, new_time: float) -> None:
        if new_time < self._time:
            raise ValueError("Simulation time cannot move backwards")
        self._time = new_time
