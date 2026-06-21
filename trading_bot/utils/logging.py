"""Logging helpers for the trading bot."""

import logging
from pathlib import Path


LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(log_dir: Path, level: int = logging.INFO) -> None:
    """Configure console and file logging for the application.

    Args:
        log_dir: Directory where the application log file is written.
        level: Logging level used by all configured handlers.
    """

    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "trading_bot.log"),
        ],
        force=True,
    )
