"""Tests for strategy behavior."""

import pandas as pd

from trading_bot.config.settings import StrategyConfig
from trading_bot.strategy.base import SignalSide
from trading_bot.strategy.moving_average import MovingAverageCrossoverStrategy


def test_moving_average_strategy_emits_runtime_agnostic_signals() -> None:
    """Strategy emits signal sides from market data only."""

    market_data = pd.DataFrame(
        {"close": [10, 9, 8, 9, 10, 11, 12]},
        index=pd.date_range("2026-01-01", periods=7, freq="h", tz="UTC"),
    )
    strategy = MovingAverageCrossoverStrategy(
        StrategyConfig(fast_window=2, slow_window=3, trade_size=1.0),
    )

    signals = strategy.generate_signals(market_data)

    assert SignalSide.BUY in set(signals)
