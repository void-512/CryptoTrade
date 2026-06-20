"""Broker abstractions for live execution."""

from abc import ABC, abstractmethod

from trading_bot.strategy.base import Signal


class Broker(ABC):
    """Interface implemented by live trading brokers."""

    @abstractmethod
    def submit_signal(self, symbol: str, signal: Signal) -> None:
        """Submit a strategy signal to the broker."""
