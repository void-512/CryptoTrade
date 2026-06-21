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


## Performance analysis

`PerformanceAnalyzer` computes total return, annual return, annual volatility,
Sharpe Ratio annualized with 365 trading days, maximum drawdown, win rate,
profit factor, number of trades, average holding time, and average trade return.
It returns metrics as a dictionary and can print a formatted performance summary.


## Strategy comparison chart

Use `export_strategy_vs_buy_and_hold` to compare the
`DoubleMovingAverageRSIStrategy` equity curve with a buy-and-hold BTC/USDT curve.
Both curves start from 10,000 USDT by default. The chart is saved to
`plots/backtest.png`, and the plotted data is exported to `plots/backtest.csv`.


## Vectorbt backtest settings

`VectorbtBacktestEngine` runs with 10,000 USDT initial cash, 0.04% commission,
and 0.01% slippage by default. It passes the CCXT timeframe to vectorbt as the
portfolio frequency so annualized metrics such as Sharpe, Calmar, Omega, and
Sortino ratios can be computed without frequency warnings.
