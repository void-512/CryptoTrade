"""Comparison chart utilities for strategy and buy-and-hold backtests."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_INITIAL_CAPITAL = 10_000.0
DEFAULT_CHART_PATH = Path("plots/backtest.png")
DEFAULT_CSV_PATH = Path("plots/backtest.csv")


def export_strategy_vs_buy_and_hold(
    strategy_equity_curve: pd.DataFrame,
    market_data: pd.DataFrame,
    output_path: str | Path = DEFAULT_CHART_PATH,
    csv_path: str | Path = DEFAULT_CSV_PATH,
    initial_capital: float = DEFAULT_INITIAL_CAPITAL,
) -> pd.DataFrame:
    """Plot and export strategy equity versus buy-and-hold equity.

    Args:
        strategy_equity_curve: DataFrame with ``timestamp`` and
            ``portfolio_value`` columns for ``DoubleMovingAverageRSIStrategy``.
        market_data: OHLCV DataFrame with ``timestamp`` and ``close`` columns.
        output_path: Destination PNG path. Defaults to ``plots/backtest.png``.
        csv_path: Destination CSV path for the plotted data.
        initial_capital: Starting capital for both curves in USDT.

    Returns:
        DataFrame containing timestamps, strategy equity, and buy-and-hold
        equity values used in the chart.
    """

    comparison = build_strategy_vs_buy_and_hold_data(
        strategy_equity_curve=strategy_equity_curve,
        market_data=market_data,
        initial_capital=initial_capital,
    )
    _save_comparison_csv(comparison, csv_path)
    _plot_comparison_chart(comparison, output_path)
    return comparison


def build_strategy_vs_buy_and_hold_data(
    strategy_equity_curve: pd.DataFrame,
    market_data: pd.DataFrame,
    initial_capital: float = DEFAULT_INITIAL_CAPITAL,
) -> pd.DataFrame:
    """Build aligned strategy and buy-and-hold portfolio value curves."""

    strategy = _prepare_strategy_equity(strategy_equity_curve, initial_capital)
    market = _prepare_market_data(market_data)

    first_close = float(market["close"].iloc[0])
    if first_close <= 0:
        raise ValueError("First close price must be greater than zero")

    buy_and_hold_units = initial_capital / first_close
    market["buy_and_hold_portfolio_value"] = buy_and_hold_units * market["close"]

    comparison = pd.merge(
        strategy,
        market.loc[:, ["timestamp", "buy_and_hold_portfolio_value"]],
        on="timestamp",
        how="inner",
    )
    if comparison.empty:
        raise ValueError("Strategy equity and market data timestamps do not overlap")
    return comparison


def _prepare_strategy_equity(
    strategy_equity_curve: pd.DataFrame,
    initial_capital: float,
) -> pd.DataFrame:
    """Validate and normalize strategy portfolio values."""

    required_columns = {"timestamp", "portfolio_value"}
    missing_columns = required_columns - set(strategy_equity_curve.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing strategy equity columns: {missing}")

    strategy = strategy_equity_curve.loc[:, ["timestamp", "portfolio_value"]].copy()
    strategy["timestamp"] = pd.to_datetime(strategy["timestamp"], utc=True)
    strategy = strategy.rename(
        columns={"portfolio_value": "strategy_portfolio_value"}
    )
    strategy = strategy.sort_values("timestamp").dropna()
    if strategy.empty:
        raise ValueError("Strategy equity curve cannot be empty")

    first_value = float(strategy["strategy_portfolio_value"].iloc[0])
    if first_value <= 0:
        raise ValueError("First strategy portfolio value must be greater than zero")
    strategy["strategy_portfolio_value"] = (
        strategy["strategy_portfolio_value"] / first_value * initial_capital
    )
    return strategy.reset_index(drop=True)


def _prepare_market_data(market_data: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize market close prices."""

    required_columns = {"timestamp", "close"}
    missing_columns = required_columns - set(market_data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing market data columns: {missing}")

    market = market_data.loc[:, ["timestamp", "close"]].copy()
    market["timestamp"] = pd.to_datetime(market["timestamp"], utc=True)
    market["close"] = market["close"].astype(float)
    market = market.sort_values("timestamp").dropna()
    if market.empty:
        raise ValueError("Market data cannot be empty")
    return market.reset_index(drop=True)


def _save_comparison_csv(comparison: pd.DataFrame, csv_path: str | Path) -> None:
    """Export comparison chart data to CSV."""

    destination = Path(csv_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(destination, index=False)


def _plot_comparison_chart(
    comparison: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Save the strategy versus buy-and-hold comparison chart."""

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.plot(
        comparison["timestamp"],
        comparison["strategy_portfolio_value"],
        label="DoubleMovingAverageRSIStrategy",
    )
    axis.plot(
        comparison["timestamp"],
        comparison["buy_and_hold_portfolio_value"],
        label="Buy and Hold",
    )
    axis.set_title("Strategy vs Buy and Hold")
    axis.set_xlabel("Date")
    axis.set_ylabel("Portfolio Value (USDT)")
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(destination)
    plt.close(figure)
