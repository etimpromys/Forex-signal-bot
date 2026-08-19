import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
from typing import Optional
import config

def is_data_stale(df, max_age_minutes=None):
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

def fetch_ohlc(ticker, interval=None, period=None):
    pass

def fetch_all_pairs():
    pass
