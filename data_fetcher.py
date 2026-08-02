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

    # Normalize to a timezone-aware UTC timestamp for a safe comparison,
    # since yfinance's index tz can vary by ticker/environment.
    if last_timestamp.tzinfo is None:
        last_timestamp = last_timestamp.tz_localize("UTC")
    else:
        last_timestamp = last_timestamp.tz_convert("UTC")

    age_minutes = (datetime.now(timezone.utc) - last_timestamp).total_seconds() / 60
    return age_minutes > max_age_minutes


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
    Returns a dict of {ticker: DataFrame}, skipping any pair that failed to
    fetch, has insufficient history, or has stale data (e.g. market closed
    over the weekend -- yfinance keeps returning the last real candle rather
    than erroring, so this check prevents the bot from acting on frozen prices).
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