import unittest

from TCP_logic.config import SenderConfig
from TCP_logic.experiment import run_single_experiment
from TCP_logic.integration import create_integrated_stack


class IntegrationTests(unittest.TestCase):
    def test_integrated_stack_tahoe_smoke(self) -> None:
        config = SenderConfig(total_packets=8, timeout_interval=0.6)

        result = run_single_experiment(
            algorithm="Tahoe",
            loss_probability=0.0,
            seed=11,
            config=config,
            simulation_factory=lambda loss, seed: create_integrated_stack(
                loss_probability=loss,
                seed=seed,
                config=config,
            ),
        )

        self.assertTrue(result.completed)
        self.assertGreater(result.throughput, 0.0)
        self.assertGreaterEqual(result.goodput, 0.0)
        self.assertLessEqual(result.goodput, 1.0)
        self.assertGreaterEqual(result.avg_delay, 0.0)
        self.assertGreaterEqual(result.jitter, 0.0)


if __name__ == "__main__":
    unittest.main()
