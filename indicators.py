"""
indicators.py
Technical indicator calculations: RSI, MACD, EMA, ATR.

Uses the lightweight pure-Python `ta` library (no compiled dependencies like TA-Lib,
which keeps this GitHub-Actions-friendly with a plain `pip install`).
"""

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange

import config


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes an OHLC DataFrame and appends indicator columns:
    rsi, ema_fast, ema_slow, macd, macd_signal, macd_hist, atr

    Returns a new DataFrame (does not mutate the input in place).
    """
    out = df.copy()

    # RSI
    rsi = RSIIndicator(close=out["close"], window=config.RSI_PERIOD)
    out["rsi"] = rsi.rsi()

    # EMA fast/slow
    out["ema_fast"] = EMAIndicator(close=out["close"], window=config.EMA_FAST).ema_indicator()
    out["ema_slow"] = EMAIndicator(close=out["close"], window=config.EMA_SLOW).ema_indicator()

    # MACD
    macd = MACD(
        close=out["close"],
        window_fast=config.MACD_FAST,
        window_slow=config.MACD_SLOW,
        window_sign=config.MACD_SIGNAL,
    )
    out["macd"] = macd.macd()
    out["macd_signal"] = macd.macd_signal()
    out["macd_hist"] = macd.macd_diff()

    # ATR (needs high/low/close)
    atr = AverageTrueRange(high=out["high"], low=out["low"], close=out["close"], window=config.ATR_PERIOD)
    out["atr"] = atr.average_true_range()

    return out.dropna()


def latest_snapshot(df: pd.DataFrame) -> dict:
    """
    Extracts the most recent row of indicator values as a plain dict,
    for use in strategy logic, risk calcs, and Claude reasoning prompts.
    """
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    return {
        "close": round(float(last["close"]), 5),
        "rsi": round(float(last["rsi"]), 2),
        "ema_fast": round(float(last["ema_fast"]), 5),
        "ema_slow": round(float(last["ema_slow"]), 5),
        "macd": round(float(last["macd"]), 5),
        "macd_signal": round(float(last["macd_signal"]), 5),
        "macd_hist": round(float(last["macd_hist"]), 5),
        "macd_hist_prev": round(float(prev["macd_hist"]), 5),
        "atr": round(float(last["atr"]), 5),
    }
