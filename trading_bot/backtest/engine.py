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
        minimum_candles: int | None = None,
    ) -> None:
        """Inject dependencies and portfolio simulation settings.

        Args:
            data_provider: Source for OHLCV market data.
            strategy: Runtime-agnostic strategy that emits signal sides.
            initial_cash: Starting portfolio value in quote currency.
            fees: Proportional commission rate. ``0.0004`` is 0.04%.
            slippage: Proportional slippage rate. ``0.0001`` is 0.01%.
            minimum_candles: Minimum prepared candles required before running.
        """

        self._data_provider = data_provider
        self._strategy = strategy
        self._initial_cash = initial_cash
        self._fees = fees
        self._slippage = slippage
        self._minimum_candles = minimum_candles

    def run(self, symbol: str, timeframe: str, limit: int) -> vbt.Portfolio:
        """Run a vectorbt portfolio simulation with a configured frequency."""

        market_data = self._data_provider.get_ohlcv(symbol, timeframe, limit)
        market_data = self._prepare_market_data(market_data)
        self._validate_history_length(market_data)
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

    def _validate_history_length(self, market_data: pd.DataFrame) -> None:
        """Raise a clear error before producing one-candle empty results."""

        required = self._minimum_candles or self._strategy_lookback() + 2
        if len(market_data) < required:
            raise ValueError(
                f"Backtest requires at least {required} candles, but received "
                f"{len(market_data)}. Increase the market-data limit or use a "
                "timeframe with sufficient exchange history."
            )

    def _strategy_lookback(self) -> int:
        """Infer a conservative lookback from common strategy config fields."""

        config = getattr(self._strategy, "_config", None)
        windows = [
            getattr(config, "fast_window", 0),
            getattr(config, "slow_window", 0),
            getattr(config, "rsi_window", 0),
        ]
        return max([int(window) for window in windows if window] or [0])

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
