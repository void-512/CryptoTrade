"""CCXT market data provider for Crypto.com and other exchanges."""

import logging
from typing import Any

import ccxt
import pandas as pd

from trading_bot.config.settings import ExchangeConfig
from trading_bot.data.provider import MarketDataProvider

LOGGER = logging.getLogger(__name__)


class CcxtMarketDataProvider(MarketDataProvider):
    """Fetch OHLCV data through CCXT."""

    def __init__(self, config: ExchangeConfig) -> None:
        """Create a CCXT-backed data provider.

        Args:
            config: Exchange connection settings.
        """

        exchange_class = getattr(ccxt, config.exchange_id)
        params: dict[str, Any] = {"enableRateLimit": True}
        if config.api_key and config.api_secret:
            params.update({"apiKey": config.api_key, "secret": config.api_secret})
        self._exchange = exchange_class(params)
        if config.sandbox and hasattr(self._exchange, "set_sandbox_mode"):
            self._exchange.set_sandbox_mode(True)

    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Return OHLCV candles as a timestamp-indexed DataFrame."""

        LOGGER.info("Fetching %s %s candles from CCXT", symbol, timeframe)
        rows = self._exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        frame = pd.DataFrame(
            rows,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        frame = frame.sort_values("timestamp").drop_duplicates("timestamp")
        return frame.set_index("timestamp")
