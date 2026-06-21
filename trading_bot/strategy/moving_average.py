"""Moving-average crossover strategy implementation."""

import pandas as pd

from trading_bot.config.settings import StrategyConfig
from trading_bot.strategy.base import Signal, SignalSide, Strategy


class MovingAverageCrossoverStrategy(Strategy):
    """Generate buy/sell signals from fast and slow moving averages."""

    def __init__(self, config: StrategyConfig) -> None:
        """Initialize the strategy with tunable windows and trade size."""

        if config.fast_window >= config.slow_window:
            raise ValueError("fast_window must be smaller than slow_window")
        self._config = config

    def generate_signals(self, market_data: pd.DataFrame) -> pd.Series:
        """Return BUY/SELL/HOLD signals without knowing the runtime mode."""

        close = market_data["close"]
        fast = close.rolling(self._config.fast_window).mean()
        slow = close.rolling(self._config.slow_window).mean()
        previous_fast = fast.shift(1)
        previous_slow = slow.shift(1)

        signals = pd.Series(SignalSide.HOLD, index=market_data.index, dtype="object")
        signals[(fast > slow) & (previous_fast <= previous_slow)] = SignalSide.BUY
        signals[(fast < slow) & (previous_fast >= previous_slow)] = SignalSide.SELL
        return signals

    def latest_signal(self, market_data: pd.DataFrame) -> Signal:
        """Return the latest signal and configured order size."""

        side = self.generate_signals(market_data).iloc[-1]
        return Signal(side=side, size=self._config.trade_size)
