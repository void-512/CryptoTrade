"""Live trading engine orchestration."""

import logging

from trading_bot.broker.base import Broker
from trading_bot.data.provider import MarketDataProvider
from trading_bot.strategy.base import Strategy

LOGGER = logging.getLogger(__name__)


class LiveTradingEngine:
    """Coordinate market data, strategy evaluation, and broker execution."""

    def __init__(
        self,
        data_provider: MarketDataProvider,
        strategy: Strategy,
        broker: Broker,
    ) -> None:
        """Inject dependencies required for live trading."""

        self._data_provider = data_provider
        self._strategy = strategy
        self._broker = broker

    def run_once(self, symbol: str, timeframe: str, limit: int) -> None:
        """Evaluate one live trading cycle and submit any actionable signal."""

        LOGGER.info("Running one live trading cycle for %s", symbol)
        market_data = self._data_provider.get_ohlcv(symbol, timeframe, limit)
        signal = self._strategy.latest_signal(market_data)
        self._broker.submit_signal(symbol, signal)
