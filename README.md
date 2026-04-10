# PA-2 TCP Discrete Event Simulator

## Project Status

Project implementation is complete and integrated.

- Theo completed the DES core (`tcp_des`): clock, events, queue, simulator loop, network/loss model, metrics, and base abstractions.
- Leo completed TCP logic (`TCP_logic`): Tahoe, Reno, experiments, and analysis.
- Integration adapters connect both sides and run end-to-end experiments.
- Unified and component-level run scripts are available.

## What Is Included

- Discrete event simulator with event types: `SEND`, `RECEIVE`, `ACK`, `TIMEOUT`, `DROP`
- Fixed RTT model and configurable packet loss probability sweep
- Performance metrics: throughput, goodput, average delay, delay jitter
- TCP Tahoe and TCP Reno sender behavior with integration tests
- Graph generation for Tahoe vs Reno comparison

## Finalized Assumptions

- Loss is applied to data packets only; ACKs are not dropped.
- Timeout is modeled per packet transmission; stale timeout events are ignored after ACK.
- Delay jitter uses population standard deviation (`statistics.pstdev`).

## Run

From the project root (recommended full run):

```bash
./run_all.sh
```

This runs merged tests, Person 1 demo metrics, and Person 2 integration sweep/plot.

## Output

- Test suites for DES core and integrated TCP behavior
- Console summary comparing Tahoe vs Reno
- Plot image saved to `outputs/tahoe_vs_reno_metrics.png`
