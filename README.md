# CryptoTrade

Clean architecture Python 3.12 algorithmic trading project for Crypto.com.

## Stack

- Backtesting: vectorbt
- Live trading: vn.py adapter boundary
- Exchange and market data: Crypto.com through CCXT
- Plotting: matplotlib
- Metrics and data manipulation: numpy and pandas

## Architecture

Strategies depend only on market data and emit runtime-agnostic signals. Backtest
and live engines receive data providers, strategies, and brokers through
dependency injection so strategy code does not know whether it is running in a
backtest or live environment.

## Usage

```bash
python -m trading_bot.main backtest
python -m trading_bot.main live
```

## Historical data download

Download one year of Crypto.com BTC/USDT 1-minute OHLCV candles to CSV:

```bash
python -m trading_bot.data.downloader --symbol BTC/USDT --timeframe 1m --output trading_bot/data/btc_usdt_1m.csv
```

The downloader is reusable for any CCXT symbol and timeframe. It enables CCXT
rate limiting, writes the required `timestamp,open,high,low,close,volume`
columns, and resumes automatically by reading the latest timestamp already saved
in the destination CSV.
