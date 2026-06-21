"""Vectorbt backtesting engine."""

import logging

import pandas as pd
import vectorbt as vbt

from trading_bot.data.provider import MarketDataProvider
from trading_bot.strategy.base import SignalSide, Strategy

LOGGER = logging.getLogger(__name__)


class VectorbtBacktestEngine:
    """Run strategy backtests using vectorbt."""

    def __init__(
        self,
        data_provider: MarketDataProvider,
        strategy: Strategy,
        initial_cash: float = 10_000.0,
        fees: float = 0.0004,
        slippage: float = 0.0001,
    ) -> None:
        """Inject dependencies and portfolio simulation settings.

        Args:
            data_provider: Source for OHLCV market data.
            strategy: Runtime-agnostic strategy that emits signal sides.
            initial_cash: Starting portfolio value in quote currency.
            fees: Proportional commission rate. ``0.0004`` is 0.04%.
            slippage: Proportional slippage rate. ``0.0001`` is 0.01%.
        """

        self._data_provider = data_provider
        self._strategy = strategy
        self._initial_cash = initial_cash
        self._fees = fees
        self._slippage = slippage

    def run(self, symbol: str, timeframe: str, limit: int) -> vbt.Portfolio:
        """Run a vectorbt portfolio simulation with a configured frequency."""

        market_data = self._data_provider.get_ohlcv(symbol, timeframe, limit)
        market_data = self._prepare_market_data(market_data)
        signals = self._strategy.generate_signals(market_data).reindex(
            market_data.index
        )
        entries = signals == SignalSide.BUY
        exits = signals == SignalSide.SELL
        frequency = self._timeframe_to_frequency(timeframe)

        LOGGER.info(
            "Running vectorbt backtest for %s with %s candles at %s frequency",
            symbol,
            len(market_data),
            frequency,
        )
        return vbt.Portfolio.from_signals(
            market_data["close"],
            entries,
            exits,
            init_cash=self._initial_cash,
            fees=self._fees,
            slippage=self._slippage,
            freq=frequency,
        )

    @staticmethod
    def stats(portfolio: vbt.Portfolio) -> pd.Series:
        """Return vectorbt portfolio performance statistics."""

        return portfolio.stats()

    @staticmethod
    def _prepare_market_data(market_data: pd.DataFrame) -> pd.DataFrame:
        """Sort, deduplicate, and validate OHLCV data before simulation."""

        if "close" not in market_data.columns:
            raise ValueError("Market data must contain a close column")
        prepared = market_data.copy()
        prepared.index = pd.to_datetime(prepared.index, utc=True)
        prepared = prepared.sort_index()
        prepared = prepared.loc[~prepared.index.duplicated(keep="last")]
        prepared = prepared.dropna(subset=["close"])
        if prepared.empty:
            raise ValueError("Market data is empty after preparation")
        prepared["close"] = prepared["close"].astype(float)
        return prepared

    @staticmethod
    def _timeframe_to_frequency(timeframe: str) -> str:
        """Convert CCXT-style timeframes to pandas/vectorbt frequency strings."""

        normalized = timeframe.strip().lower()
        if not normalized:
            raise ValueError("Timeframe cannot be empty")
        units = {
            "m": "min",
            "h": "h",
            "d": "D",
            "w": "W",
        }
        unit = normalized[-1]
        amount = normalized[:-1]
        if unit not in units or not amount.isdigit():
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        return f"{amount}{units[unit]}"
