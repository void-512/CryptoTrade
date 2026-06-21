"""Strategy interfaces and shared signal models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class SignalSide(str, Enum):
    """Trade signal direction."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class Signal:
    """Trading signal emitted by a strategy."""

    side: SignalSide
    size: float


class Strategy(ABC):
    """Runtime-agnostic strategy interface."""

    @abstractmethod
    def generate_signals(self, market_data: pd.DataFrame) -> pd.Series:
        """Return a time series of strategy signal sides."""

    @abstractmethod
    def latest_signal(self, market_data: pd.DataFrame) -> Signal:
        """Return the latest actionable signal from market data."""
