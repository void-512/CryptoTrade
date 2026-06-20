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
