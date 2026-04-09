Initial Design Plan - Splitting the Work.

Person 1 — Simulator Core & Network

Simulated clock
Event queue (priority queue by time)
Packet & ACK data structures
Sender/receiver abstractions (interfaces/base classes)
Network model: propagation delay, loss model (random drop by probability)
Metric collection hooks (packet sent, received, dropped, timestamps)
Logging/output utilities

Person 2 — TCP Logic & Analysis

TCP Tahoe state machine (slow start, congestion avoidance, timeout)
TCP Reno state machine (+ fast retransmit/fast recovery)
Duplicate ACK handling
Timeout behavior
Experiment runner (sweep over loss probabilities, call Person 1's simulator)
Graph generation (throughput, goodput, delay, jitter vs. loss probability)
Written comparison/report


===================================================================================


## Shared Design Decisions

These are the agreed-upon assumptions both implementations must follow before writing any code.

---

### Events

The simulator handles the following event types:

- `SEND` — sender transmits a packet onto the network
- `RECEIVE` — packet arrives at the receiver
- `ACK` — acknowledgment sent back to the sender
- `TIMEOUT` — retransmission timer expires for a packet
- `DROP` — packet is silently lost in the network

---

### RTT Model

- **Fixed RTT** is used for simplicity.
- Propagation delay is constant and symmetric.
- No queuing delay or variable latency is modeled.

---

### Loss Model

- **Drop on receive, uniform random.**
- Each packet is independently dropped with probability `p` upon arrival at the receiver.
- The sender receives no signal — it detects loss via timeout or duplicate ACKs.
- `p` is a configurable parameter swept across experiments.

---

### Performance Metrics

| Metric | Formula |
|---|---|
| Throughput | `unique_packets_received / total_simulated_time` (packets/sec) |
| Goodput | `unique_packets_delivered / total_packets_sent` (ratio 0–1) |
| Average Delay | `mean(time_ACKed − time_first_sent)` across all delivered packets |
| Delay Jitter | `std_dev(individual_delays)` |

> **Note:** retransmissions count toward `total_packets_sent` but not toward `unique_packets_delivered`.  
> Delay is measured from **first transmission**, not from retransmissions.

**Per-packet tracking required:**
```
packet_id → { time_first_sent, time_acked, retransmit_count }
```

---

### Module Interface

Person 1 (simulator core) exposes:

```python
class Simulator:
    def schedule_event(time, event_type, data)
    def get_current_time() -> float
    def run()

class Network:
    def send_packet(packet)
    def send_ack(ack)

class MetricsCollector:
    def record_sent(packet_id, time)
    def record_received(packet_id, time)
    def record_dropped(packet_id)
    def record_retransmit(packet_id)
    def report() -> dict   # returns throughput, goodput, avg_delay, jitter
```

Person 2 (TCP logic) implements:

```python
class TCPSender:
    def on_ack_received(ack)
    def on_timeout(packet_id)
    def send_next()

class TCPTahoe(TCPSender): ...
class TCPReno(TCPSender): ...
```

> **Rule:** Person 2 calls into Person 1's API only (`schedule_event`, `send_packet`, `MetricsCollector`).  
> Person 1 calls into Person 2's callbacks only (`on_ack_received`, `on_timeout`).  
> Neither side reaches into the other's internals.