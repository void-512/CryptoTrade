"""Vectorbt backtesting engine."""

import logging

import pandas as pd
import vectorbt as vbt

from trading_bot.data.provider import MarketDataProvider
from trading_bot.strategy.base import SignalSide, Strategy

LOGGER = logging.getLogger(__name__)


class VectorbtBacktestEngine:
    """Run strategy backtests using vectorbt."""

    def __init__(self, data_provider: MarketDataProvider, strategy: Strategy) -> None:
        """Inject the data provider and runtime-agnostic strategy."""

        self._data_provider = data_provider
        self._strategy = strategy

    def run(self, symbol: str, timeframe: str, limit: int) -> vbt.Portfolio:
        """Run a vectorbt portfolio simulation."""

        market_data = self._data_provider.get_ohlcv(symbol, timeframe, limit)
        signals = self._strategy.generate_signals(market_data)
        entries = signals == SignalSide.BUY
        exits = signals == SignalSide.SELL
        LOGGER.info("Running vectorbt backtest for %s", symbol)
        return vbt.Portfolio.from_signals(market_data["close"], entries, exits)

    @staticmethod
    def stats(portfolio: vbt.Portfolio) -> pd.Series:
        """Return vectorbt portfolio performance statistics."""

        return portfolio.stats()
