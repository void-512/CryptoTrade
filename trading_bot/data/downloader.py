"""Reusable historical OHLCV downloader backed by CCXT."""

import argparse
import logging
import time
from pathlib import Path
from typing import Any, Protocol

import ccxt
import pandas as pd

LOGGER = logging.getLogger(__name__)
OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]
DEFAULT_OUTPUT = Path("trading_bot/data/btc_usdt_1m.csv")


class OhlcvExchange(Protocol):
    """Minimal CCXT exchange protocol required by the downloader."""

    rateLimit: int

    def milliseconds(self) -> int:
        """Return the current exchange clock in milliseconds."""

    def parse_timeframe(self, timeframe: str) -> int:
        """Return a timeframe duration in seconds."""

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        since: int | None = None,
        limit: int | None = None,
    ) -> list[list[Any]]:
        """Fetch OHLCV rows from the exchange."""


class HistoricalDataDownloader:
    """Download resumable historical OHLCV data from a CCXT exchange."""

    def __init__(
        self,
        exchange: OhlcvExchange,
        limit_per_request: int = 300,
    ) -> None:
        """Initialize the downloader.

        Args:
            exchange: CCXT-compatible exchange instance.
            limit_per_request: Maximum candles requested per API call.
        """

        self._exchange = exchange
        self._limit_per_request = limit_per_request

    def download(
        self,
        symbol: str,
        timeframe: str,
        output_path: Path,
        since_ms: int,
        until_ms: int | None = None,
    ) -> pd.DataFrame:
        """Download OHLCV candles and save them as a CSV file.

        Existing CSV files are loaded first so interrupted downloads resume from
        the candle after the latest saved timestamp.

        Args:
            symbol: Trading pair, for example ``BTC/USDT``.
            timeframe: CCXT timeframe, for example ``1m`` or ``1h``.
            output_path: CSV destination path.
            since_ms: Inclusive start timestamp in milliseconds.
            until_ms: Exclusive end timestamp in milliseconds. Defaults to now.

        Returns:
            DataFrame containing all persisted candles sorted by timestamp.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)
        timeframe_ms = self._exchange.parse_timeframe(timeframe) * 1_000
        end_ms = until_ms or self._exchange.milliseconds()
        existing = self._read_existing(output_path)
        next_since_ms = self._next_since_ms(existing, since_ms, timeframe_ms)

        LOGGER.info(
            "Downloading %s %s OHLCV from %s to %s into %s",
            symbol,
            timeframe,
            pd.to_datetime(next_since_ms, unit="ms", utc=True),
            pd.to_datetime(end_ms, unit="ms", utc=True),
            output_path,
        )

        while next_since_ms < end_ms:
            rows = self._exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=next_since_ms,
                limit=self._limit_per_request,
            )
            if not rows:
                LOGGER.info("No more candles returned for %s %s", symbol, timeframe)
                break

            batch = self._rows_to_frame(rows, end_ms)
            if batch.empty:
                break

            existing = self._merge_and_save(existing, batch, output_path)
            last_timestamp_ms = int(batch["timestamp"].max().timestamp() * 1_000)
            next_since_ms = last_timestamp_ms + timeframe_ms
            LOGGER.info("Saved %d candles to %s", len(existing), output_path)
            self._respect_rate_limit()

        return existing

    @staticmethod
    def one_year_ago_ms(exchange: OhlcvExchange) -> int:
        """Return an exchange-clock timestamp for approximately one year ago."""

        return exchange.milliseconds() - 365 * 24 * 60 * 60 * 1_000

    @staticmethod
    def _read_existing(output_path: Path) -> pd.DataFrame:
        """Read an existing CSV file or return an empty OHLCV DataFrame."""

        if not output_path.exists():
            return pd.DataFrame(columns=OHLCV_COLUMNS)
        frame = pd.read_csv(output_path, parse_dates=["timestamp"])
        return frame.loc[:, OHLCV_COLUMNS]

    @staticmethod
    def _next_since_ms(
        existing: pd.DataFrame,
        since_ms: int,
        timeframe_ms: int,
    ) -> int:
        """Compute the next timestamp to request, accounting for saved data."""

        if existing.empty:
            return since_ms
        latest_ms = int(existing["timestamp"].max().timestamp() * 1_000)
        return max(since_ms, latest_ms + timeframe_ms)

    @staticmethod
    def _rows_to_frame(rows: list[list[Any]], until_ms: int) -> pd.DataFrame:
        """Convert raw CCXT rows into a normalized OHLCV DataFrame."""

        frame = pd.DataFrame(rows, columns=OHLCV_COLUMNS)
        frame = frame[frame["timestamp"] < until_ms]
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        return frame.loc[:, OHLCV_COLUMNS]

    @staticmethod
    def _merge_and_save(
        existing: pd.DataFrame,
        batch: pd.DataFrame,
        output_path: Path,
    ) -> pd.DataFrame:
        """Merge new candles with saved candles and persist a deduplicated CSV."""

        merged = pd.concat([existing, batch], ignore_index=True)
        merged = merged.drop_duplicates(subset=["timestamp"], keep="last")
        merged = merged.sort_values("timestamp").reset_index(drop=True)
        merged.to_csv(output_path, index=False)
        return merged

    def _respect_rate_limit(self) -> None:
        """Sleep for the exchange rate-limit interval between requests."""

        delay_seconds = max(self._exchange.rateLimit, 0) / 1_000
        if delay_seconds:
            time.sleep(delay_seconds)


def create_cryptocom_exchange() -> OhlcvExchange:
    """Create a rate-limited CCXT Crypto.com exchange instance."""

    return ccxt.cryptocom({"enableRateLimit": True})


def build_parser() -> argparse.ArgumentParser:
    """Build the downloader command-line parser."""

    parser = argparse.ArgumentParser(description="Download historical OHLCV data")
    parser.add_argument("--symbol", default="BTC/USDT", help="Trading pair")
    parser.add_argument("--timeframe", default="1m", help="CCXT timeframe")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="CSV path")
    parser.add_argument("--limit", type=int, default=300, help="Candles per request")
    return parser


def main() -> None:
    """Download one year of BTC/USDT 1-minute candles by default."""

    args = build_parser().parse_args()
    exchange = create_cryptocom_exchange()
    downloader = HistoricalDataDownloader(exchange, limit_per_request=args.limit)
    downloader.download(
        symbol=args.symbol,
        timeframe=args.timeframe,
        output_path=args.output,
        since_ms=HistoricalDataDownloader.one_year_ago_ms(exchange),
    )


if __name__ == "__main__":
    main()
