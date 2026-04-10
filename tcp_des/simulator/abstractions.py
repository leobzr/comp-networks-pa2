"""Base abstractions for sender and receiver logic integration."""

from abc import ABC, abstractmethod

from .packet import Ack, Packet


class BaseSender(ABC):
    """Callback surface Leo implements for Tahoe and Reno senders."""

    @abstractmethod
    def on_ack_received(self, ack: Ack) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_timeout(self, packet_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_next(self) -> None:
        raise NotImplementedError


class BaseReceiver(ABC):
    """Receiver callback invoked by simulator when a packet arrives."""

    @abstractmethod
    def on_packet_received(self, packet: Packet) -> Ack | None:
        raise NotImplementedError
