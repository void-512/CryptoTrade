"""Performance analysis utilities for backtest results."""

from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 365


class PerformanceAnalyzer:
    """Compute and display portfolio and trade performance metrics."""

    def analyze(
        self,
        portfolio_value: pd.DataFrame,
        trade_history: pd.DataFrame,
        daily_returns: pd.DataFrame | None = None,
    ) -> dict[str, object]:
        """Return a dictionary of performance metrics.

        Args:
            portfolio_value: DataFrame containing ``timestamp`` and
                ``portfolio_value`` columns.
            trade_history: DataFrame containing closed trade records. The
                analyzer expects a ``pnl`` column for win/loss metrics and uses
                ``entry_timestamp`` plus ``exit_timestamp`` when available for
                average holding time.
            daily_returns: Optional DataFrame containing ``timestamp`` and
                ``daily_return`` columns. If omitted, daily returns are derived
                from ``portfolio_value``.
        """

        values = self._prepare_portfolio_value(portfolio_value)
        returns = self._prepare_daily_returns(values, daily_returns)
        trades = trade_history.copy()

        total_return = self._total_return(values)
        annual_return = self._annual_return(values, total_return)
        annual_volatility = self._annual_volatility(returns)
        sharpe_ratio = self._sharpe_ratio(returns)
        maximum_drawdown = self._maximum_drawdown(values)

        metrics: dict[str, object] = {
            "total_return": total_return,
            "annual_return": annual_return,
            "annual_volatility": annual_volatility,
            "sharpe_ratio": sharpe_ratio,
            "maximum_drawdown": maximum_drawdown,
            "win_rate": self._win_rate(trades),
            "profit_factor": self._profit_factor(trades),
            "number_of_trades": int(len(trades)),
            "average_holding_time": self._average_holding_time(trades),
            "average_trade_return": self._average_trade_return(trades),
        }
        return metrics

    def format_summary(self, metrics: dict[str, object]) -> str:
        """Format performance metrics into a human-readable text summary."""

        average_holding_time = metrics["average_holding_time"]
        if isinstance(average_holding_time, pd.Timedelta):
            holding_time = str(average_holding_time)
        else:
            holding_time = "N/A"

        return "\n".join(
            [
                "Performance Summary",
                "===================",
                f"Total Return: {self._format_percent(metrics['total_return'])}",
                f"Annual Return: {self._format_percent(metrics['annual_return'])}",
                "Annual Volatility: "
                f"{self._format_percent(metrics['annual_volatility'])}",
                f"Sharpe Ratio: {self._format_number(metrics['sharpe_ratio'])}",
                "Maximum Drawdown: "
                f"{self._format_percent(metrics['maximum_drawdown'])}",
                f"Win Rate: {self._format_percent(metrics['win_rate'])}",
                f"Profit Factor: {self._format_number(metrics['profit_factor'])}",
                f"Number of Trades: {metrics['number_of_trades']}",
                f"Average Holding Time: {holding_time}",
                "Average Trade Return: "
                f"{self._format_percent(metrics['average_trade_return'])}",
            ]
        )

    def print_summary(self, metrics: dict[str, object]) -> None:
        """Print a nicely formatted performance summary."""

        print(self.format_summary(metrics))

    @staticmethod
    def _prepare_portfolio_value(portfolio_value: pd.DataFrame) -> pd.DataFrame:
        """Validate and sort portfolio values."""

        required_columns = {"timestamp", "portfolio_value"}
        missing_columns = required_columns - set(portfolio_value.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing portfolio columns: {missing}")

        values = portfolio_value.loc[:, ["timestamp", "portfolio_value"]].copy()
        values["timestamp"] = pd.to_datetime(values["timestamp"], utc=True)
        values = values.sort_values("timestamp").dropna(subset=["portfolio_value"])
        if values.empty:
            raise ValueError("Portfolio value data cannot be empty")
        return values.reset_index(drop=True)

    @staticmethod
    def _prepare_daily_returns(
        portfolio_value: pd.DataFrame,
        daily_returns: pd.DataFrame | None,
    ) -> pd.Series:
        """Use supplied daily returns or derive them from portfolio values."""

        if daily_returns is not None:
            if "daily_return" not in daily_returns.columns:
                raise ValueError("Missing daily returns column: daily_return")
            return daily_returns["daily_return"].dropna().astype(float)

        daily_value = portfolio_value.copy()
        daily_value = daily_value.set_index("timestamp").resample("1D").last().dropna()
        return daily_value["portfolio_value"].pct_change().dropna().astype(float)

    @staticmethod
    def _total_return(portfolio_value: pd.DataFrame) -> float:
        """Calculate total return from first to last portfolio value."""

        starting_value = float(portfolio_value["portfolio_value"].iloc[0])
        ending_value = float(portfolio_value["portfolio_value"].iloc[-1])
        if starting_value == 0:
            return float("nan")
        return ending_value / starting_value - 1

    @staticmethod
    def _annual_return(portfolio_value: pd.DataFrame, total_return: float) -> float:
        """Annualize total return using a 365-day calendar year."""

        start = portfolio_value["timestamp"].iloc[0]
        end = portfolio_value["timestamp"].iloc[-1]
        elapsed_days = max((end - start).total_seconds() / 86_400, 0)
        if elapsed_days == 0 or np.isnan(total_return):
            return total_return
        return (1 + total_return) ** (TRADING_DAYS_PER_YEAR / elapsed_days) - 1

    @staticmethod
    def _annual_volatility(daily_returns: pd.Series) -> float:
        """Annualize daily return volatility using 365 trading days."""

        if daily_returns.empty:
            return 0.0
        return float(daily_returns.std(ddof=0) * sqrt(TRADING_DAYS_PER_YEAR))

    @staticmethod
    def _sharpe_ratio(daily_returns: pd.Series) -> float:
        """Annualize the Sharpe Ratio using 365 trading days."""

        if daily_returns.empty:
            return 0.0
        volatility = daily_returns.std(ddof=0)
        if volatility == 0 or np.isnan(volatility):
            return 0.0
        return float(daily_returns.mean() / volatility * sqrt(TRADING_DAYS_PER_YEAR))

    @staticmethod
    def _maximum_drawdown(portfolio_value: pd.DataFrame) -> float:
        """Calculate maximum peak-to-trough portfolio drawdown."""

        values = portfolio_value["portfolio_value"].astype(float)
        running_max = values.cummax()
        drawdown = values / running_max - 1
        return float(drawdown.min())

    @staticmethod
    def _win_rate(trade_history: pd.DataFrame) -> float:
        """Calculate percentage of profitable trades."""

        if trade_history.empty or "pnl" not in trade_history.columns:
            return 0.0
        pnl = trade_history["pnl"].astype(float)
        return float((pnl > 0).mean())

    @staticmethod
    def _profit_factor(trade_history: pd.DataFrame) -> float:
        """Calculate gross profits divided by gross losses."""

        if trade_history.empty or "pnl" not in trade_history.columns:
            return 0.0
        pnl = trade_history["pnl"].astype(float)
        gross_profit = pnl[pnl > 0].sum()
        gross_loss = abs(pnl[pnl < 0].sum())
        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0
        return float(gross_profit / gross_loss)

    @staticmethod
    def _average_holding_time(trade_history: pd.DataFrame) -> pd.Timedelta | None:
        """Calculate average time between trade entry and exit."""

        required_columns = {"entry_timestamp", "exit_timestamp"}
        if trade_history.empty or not required_columns.issubset(trade_history.columns):
            return None
        entry_time = pd.to_datetime(trade_history["entry_timestamp"], utc=True)
        exit_time = pd.to_datetime(trade_history["exit_timestamp"], utc=True)
        return (exit_time - entry_time).mean()

    @staticmethod
    def _average_trade_return(trade_history: pd.DataFrame) -> float:
        """Calculate average closed-trade return."""

        if trade_history.empty:
            return 0.0
        if "trade_return" in trade_history.columns:
            return float(trade_history["trade_return"].astype(float).mean())
        required_columns = {"entry_price", "exit_price"}
        if required_columns.issubset(trade_history.columns):
            entry_price = trade_history["entry_price"].astype(float)
            exit_price = trade_history["exit_price"].astype(float)
            return float((exit_price / entry_price - 1).mean())
        return 0.0

    @staticmethod
    def _format_percent(value: object) -> str:
        """Format decimal metric values as percentages."""

        if not isinstance(value, int | float) or np.isnan(value):
            return "N/A"
        return f"{value:.2%}"

    @staticmethod
    def _format_number(value: object) -> str:
        """Format numeric metric values for display."""

        if not isinstance(value, int | float):
            return "N/A"
        if np.isinf(value):
            return "inf"
        if np.isnan(value):
            return "N/A"
        return f"{value:.4f}"
