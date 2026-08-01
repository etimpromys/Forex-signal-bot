"""
data_fetcher.py
Handles market data ingestion for forex pairs.

Default implementation uses yfinance (free, no API key) which is well suited
for GitHub Actions since there's no key to manage. If you later want lower-latency
or more reliable intraday data, swap this out for OANDA or Twelve Data --
the interface (fetch_ohlc) stays the same so nothing else in the bot needs to change.
"""

import pandas as pd
import yfinance as yf
from typing import Optional
import config


def fetch_ohlc(ticker: str, interval: str = None, period: str = None) -> Optional[pd.DataFrame]:
    """
    Fetch OHLC candle data for a given forex ticker.

    Args:
        ticker: yfinance-format FX ticker, e.g. "EURUSD=X"
        interval: candle interval, e.g. "15m", "1h", "1d"
        period: how far back to pull, e.g. "5d", "1mo"

    Returns:
        DataFrame with columns [open, high, low, close, volume], indexed by datetime.
        Returns None if the fetch fails or comes back empty.
    """
    interval = interval or config.DATA_INTERVAL
    period = period or config.DATA_PERIOD

    try:
        df = yf.download(
            tickers=ticker,
            interval=interval,
            period=period,
            progress=False,
            auto_adjust=False,
        )
    except Exception as e:
        print(f"[DATA ERROR] Failed to fetch {ticker}: {e}")
        return None

    if df is None or df.empty:
        print(f"[DATA WARNING] No data returned for {ticker}")
        return None

    # yfinance sometimes returns MultiIndex columns when multiple tickers are involved
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    df = df.rename(columns={"adj close": "adj_close"})
    df = df.dropna(subset=["open", "high", "low", "close"])

    return df


def fetch_all_pairs() -> dict:
    """
    Fetch OHLC data for every pair in config.FOREX_PAIRS.
    Returns a dict of {ticker: DataFrame}, skipping any pair that failed to fetch.
    """
    data = {}
    for pair in config.FOREX_PAIRS:
        df = fetch_ohlc(pair)
        if df is not None and len(df) >= 30:  # need enough candles for indicators to be meaningful
            data[pair] = df
        else:
            print(f"[DATA SKIP] {pair} skipped (insufficient or missing data)")
    return data
