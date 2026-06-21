"""Market data provider abstractions."""

from abc import ABC, abstractmethod

import pandas as pd


class MarketDataProvider(ABC):
    """Interface for historical and live market data providers."""

    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Return OHLCV data indexed by timestamp."""
