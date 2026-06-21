"""Plotting utilities."""

from trading_bot.plots.comparison import (
    build_strategy_vs_buy_and_hold_data,
    export_strategy_vs_buy_and_hold,
)
from trading_bot.plots.performance import plot_equity_curve

__all__ = [
    "build_strategy_vs_buy_and_hold_data",
    "export_strategy_vs_buy_and_hold",
    "plot_equity_curve",
]
