"""Application entry point for backtest and live trading modes."""

import argparse
import logging
from pathlib import Path

from trading_bot.backtest.engine import VectorbtBacktestEngine
from trading_bot.broker.vnpy_broker import VnpyBroker
from trading_bot.config.settings import AppConfig
from trading_bot.data.ccxt_provider import CcxtMarketDataProvider
from trading_bot.live.engine import LiveTradingEngine
from trading_bot.plots.performance import plot_equity_curve
from trading_bot.strategy.moving_average import MovingAverageCrossoverStrategy
from trading_bot.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(description="Crypto.com trading bot")
    parser.add_argument("mode", choices=("backtest", "live"), help="Runtime mode")
    return parser


def main() -> None:
    """Run the trading bot in the requested mode."""

    config = AppConfig()
    configure_logging(config.log_dir)
    args = build_parser().parse_args()

    data_provider = CcxtMarketDataProvider(config.exchange)
    strategy = MovingAverageCrossoverStrategy(config.strategy)

    if args.mode == "backtest":
        engine = VectorbtBacktestEngine(data_provider, strategy)
        portfolio = engine.run(
            config.market_data.symbol,
            config.market_data.timeframe,
            config.market_data.limit,
        )
        LOGGER.info("Backtest stats:\n%s", engine.stats(portfolio))
        plot_equity_curve(portfolio.value(), Path("trading_bot/plots/equity_curve.png"))
        return

    broker = VnpyBroker()
    live_engine = LiveTradingEngine(data_provider, strategy, broker)
    live_engine.run_once(
        config.market_data.symbol,
        config.market_data.timeframe,
        config.market_data.limit,
    )


if __name__ == "__main__":
    main()
