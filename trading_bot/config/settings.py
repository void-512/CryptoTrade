"""Application settings and typed configuration models."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExchangeConfig:
    """Configuration required to connect to an exchange."""

    exchange_id: str = "cryptocom"
    api_key: str | None = None
    api_secret: str | None = None
    sandbox: bool = True


@dataclass(frozen=True)
class MarketDataConfig:
    """Configuration for market data retrieval."""

    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    limit: int = 500


@dataclass(frozen=True)
class StrategyConfig:
    """Configuration for the moving-average crossover strategy."""

    fast_window: int = 10
    slow_window: int = 30
    trade_size: float = 0.01


@dataclass(frozen=True)
class AppConfig:
    """Top-level application configuration."""

    exchange: ExchangeConfig = ExchangeConfig()
    market_data: MarketDataConfig = MarketDataConfig()
    strategy: StrategyConfig = StrategyConfig()
    log_dir: Path = Path("trading_bot/logs")
