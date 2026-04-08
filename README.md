Initial Design Plan - Splitting the Work.

Person 1: Base simulator + network model

Responsible for:

clock
event queue
sender/receiver abstractions
packet structure
ACK structure
loss model using packet loss probability
RTT / propagation assumptions
logging metrics


Person 2: TCP algorithms + analysis
Responsible for:

Tahoe implementation
Reno implementation
congestion control state machine
timeout behavior
duplicate ACK handling
experiment runner
graph generation
comparison writeup


Before starting the work, agree on these or you’ll waste time later:

what events exist
what assumptions the simulator uses
packet flow model
fixed RTT or variable RTT
how loss is simulated
how throughput/goodput/delay are computed
how Tahoe and Reno interfaces will plug into the simulator