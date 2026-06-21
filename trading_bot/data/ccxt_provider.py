"""CCXT market data provider for Crypto.com and other exchanges."""

import logging
import re
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
        """Return OHLCV candles as a timestamp-indexed DataFrame.

        Crypto.com can return only the currently forming candle for some
        unsupported granularities such as ``2h``. When that happens, this
        provider fetches a supported lower timeframe and resamples it locally so
        backtests receive enough history to produce useful statistics and plots.
        """

        LOGGER.info("Fetching %s %s candles from CCXT", symbol, timeframe)
        rows = self._fetch_rows(symbol, timeframe, limit)
        frame = self._rows_to_frame(rows)
        if len(frame) <= 1 and self._can_resample_from_hourly(timeframe):
            LOGGER.info(
                "Received %s %s candles; resampling from 1h data",
                len(frame),
                timeframe,
            )
            frame = self._fetch_and_resample_from_hourly(symbol, timeframe, limit)
        if frame.empty:
            raise ValueError(f"No OHLCV data returned for {symbol} {timeframe}")
        return frame.tail(limit)

    def _fetch_rows(self, symbol: str, timeframe: str, limit: int) -> list[list[Any]]:
        """Fetch OHLCV rows with a since timestamp covering the requested limit."""

        since = self._since_milliseconds(timeframe, limit)
        return self._exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
        )

    def _fetch_and_resample_from_hourly(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> pd.DataFrame:
        """Fetch 1h candles and resample them to the requested hour multiple."""

        multiplier = int(timeframe[:-1])
        hourly_limit = limit * multiplier
        hourly_rows = self._fetch_rows(symbol, "1h", hourly_limit)
        hourly = self._rows_to_frame(hourly_rows)
        if hourly.empty:
            raise ValueError(f"No 1h OHLCV data returned for {symbol}")
        return (
            hourly.resample(self._to_pandas_frequency(timeframe))
            .agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                }
            )
            .dropna(subset=["open", "high", "low", "close"])
            .tail(limit)
        )

    @staticmethod
    def _rows_to_frame(rows: list[list[Any]]) -> pd.DataFrame:
        """Convert raw CCXT OHLCV rows into a clean timestamp-indexed frame."""

        frame = pd.DataFrame(
            rows,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        if frame.empty:
            return frame.set_index(pd.DatetimeIndex([], name="timestamp"))
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        numeric_columns = ["open", "high", "low", "close", "volume"]
        frame[numeric_columns] = frame[numeric_columns].astype(float)
        frame = frame.sort_values("timestamp").drop_duplicates("timestamp")
        return frame.set_index("timestamp")

    def _since_milliseconds(self, timeframe: str, limit: int) -> int:
        """Return a starting timestamp far enough back for the requested data."""

        milliseconds = self._timeframe_to_milliseconds(timeframe)
        now = self._exchange.milliseconds()
        return now - milliseconds * max(limit, 1)

    @staticmethod
    def _timeframe_to_milliseconds(timeframe: str) -> int:
        """Convert a CCXT timeframe into milliseconds."""

        match = re.fullmatch(r"(\d+)([mhdw])", timeframe.strip().lower())
        if not match:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        amount = int(match.group(1))
        unit = match.group(2)
        unit_milliseconds = {
            "m": 60_000,
            "h": 3_600_000,
            "d": 86_400_000,
            "w": 604_800_000,
        }
        return amount * unit_milliseconds[unit]

    @staticmethod
    def _to_pandas_frequency(timeframe: str) -> str:
        """Convert a CCXT timeframe into a pandas resampling frequency."""

        match = re.fullmatch(r"(\d+)([mhdw])", timeframe.strip().lower())
        if not match:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        amount = match.group(1)
        unit = {"m": "min", "h": "h", "d": "D", "w": "W"}[match.group(2)]
        return f"{amount}{unit}"

    @staticmethod
    def _can_resample_from_hourly(timeframe: str) -> bool:
        """Return whether a timeframe can be rebuilt from 1h candles."""

        match = re.fullmatch(r"(\d+)h", timeframe.strip().lower())
        return bool(match and int(match.group(1)) > 1)
