"""Plotting utilities for market and portfolio analysis."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curve(equity: pd.Series, output_path: Path) -> None:
    """Plot an equity curve to a PNG file.

    Args:
        equity: Equity time series to plot.
        output_path: Destination image path.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(12, 6))
    equity.plot(ax=axis, title="Equity Curve")
    axis.set_xlabel("Time")
    axis.set_ylabel("Equity")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
