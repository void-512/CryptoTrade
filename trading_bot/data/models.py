"""Shared market data models."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Candle:
    """OHLCV candle from an exchange data source."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
