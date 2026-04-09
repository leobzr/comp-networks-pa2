# PA-2 TCP Discrete Event Simulator

## General

### Objective

Understand the inner workings of TCP Tahoe and TCP Reno by building and testing a discrete event simulator (DES).

### Project Split

Person 1 handles simulator core and network plumbing.

Person 2 handles TCP Tahoe/Reno logic and performance analysis.

### Shared Design Decisions

#### Events

The simulator handles these event types:

- `SEND`
- `RECEIVE`
- `ACK`
- `TIMEOUT`
- `DROP`

#### RTT Model

- Fixed RTT
- Constant symmetric propagation delay
- No queueing or variable latency

#### Loss Model

- Uniform random packet loss with probability `p`
- Sender infers loss through timeout/duplicate ACK behavior
- `p` is swept during experiments

#### Performance Metrics

| Metric | Formula |
|---|---|
| Throughput | `unique_packets_received / total_simulated_time` |
| Goodput | `unique_packets_delivered / total_packets_sent` |
| Average Delay | `mean(time_ACKed - time_first_sent)` |
| Delay Jitter | `std_dev(individual_delays)` |

Retransmissions count toward `total_packets_sent` but not `unique_packets_delivered`.

Per-packet tracking:

```
packet_id -> { time_first_sent, time_acked, retransmit_count }
```

#### Collaboration Rule

Person 2 only calls Person 1 APIs.

Person 1 only calls Person 2 callbacks.

Neither side reaches into the other side internals.

## Person One (TCP DES)

### Scope

- Simulated clock
- Event queue (priority by event time)
- Packet and ACK data structures
- Sender/receiver abstractions for handoff
- Network model (fixed propagation delay + random loss)
- Metrics hooks and report generation
- Logging/output utilities

### Finalized Person 1 Defaults

- Loss model: data packets only are dropped (ACKs are not dropped)
- Timeout model: one timeout event per packet transmission; stale timeouts ignored once ACKed
- Jitter: population standard deviation (`statistics.pstdev`)

### Run Person 1 Code

From the `tcp_des` folder:

```bash
./run.sh
```

`run.sh` installs dependencies, runs tests, then runs a dummy sender/receiver simulation that prints metrics.

## Person Two (TCP Logic and Analysis)

### Scope

- TCP Tahoe state machine (slow start, congestion avoidance, timeout)
- TCP Reno state machine (fast retransmit/fast recovery)
- Duplicate ACK handling
- Timeout behavior tuning
- Experiment runner over packet loss probabilities
- Graph generation (throughput/goodput/delay/jitter vs. loss)
- Written comparison report

### Expected Integration Surface

Person 2 should implement sender logic using the agreed callbacks:

- `on_ack_received(ack)`
- `on_timeout(packet_id)`
- `send_next()`