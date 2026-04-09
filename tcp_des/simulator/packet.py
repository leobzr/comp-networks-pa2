"""Packet data structures used by sender, receiver, and network."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Packet:
    packet_id: int
    payload_size: int = 1


@dataclass(frozen=True)
class Ack:
    ack_id: int
