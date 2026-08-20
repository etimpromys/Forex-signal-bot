"""
data_fetcher.py
Handles market data ingestion for forex pairs.

Uses yfinance (free, no API key) which is well suited for GitHub Actions
since there's no key to manage.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
from typing import Optional
import config


def is_data_stale(df: pd.DataFrame, max_age_minutes: int = None) -> bool:
    """
    Checks whether the most recent candle in the DataFrame is older than
    max_age_minutes. Used to detect frozen/weekend data from yfinance, which
    doesn't reliably signal "market closed" -- it just stops returning new
    candles, so the last one can look deceptively normal without this check.
    """
    max_age_minutes = max_age_minutes or config.MAX_DATA_AGE_MINUTES

    if df.empty:
        return True

    last_timestamp = df.index[-1]

    if last_timestamp.tzinfo is None:
        last_timestamp = last_timestamp.tz_localize("UTC")
    else:
        last_timestamp = last_timestamp.tz_convert("UTC")

    age_minutes = (datetime.now(timezone.utc) - last_timestamp).total_seconds() / 60
    return age_minutes > max_age_minutes


def fetch_ohlc(ticker: str, interval: str = None, period: str = None) -> Optional[pd.DataFrame]:
    """
    Fetch OHLC candle data for a given forex ticker.

    Returns a DataFrame with columns [open, high, low, close, volume],
    indexed by datetime. Returns None if the fetch fails or comes back empty.
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
    Returns a dict of {ticker: DataFrame}, skipping any pair that failed to
    fetch, has insufficient history, or has stale data (e.g. market closed
    over the weekend).
    """
    data = {}
    for pair in config.FOREX_PAIRS:
        df = fetch_ohlc(pair)

        if df is None or len(df) < 30:
            print(f"[DATA SKIP] {pair} skipped (insufficient or missing data)")
            continue

        if is_data_stale(df):
            last_ts = df.index[-1]
            print(f"[DATA SKIP] {pair} skipped (stale data, last candle: {last_ts} -- market likely closed)")
            continue

        data[pair] = df
    return data
