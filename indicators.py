"""
indicators.py
Technical indicator calculations: RSI, MACD, EMA, ATR, ADX.
"""

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator, ADXIndicator
from ta.volatility import AverageTrueRange

import config


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes an OHLC DataFrame and appends indicator columns:
    rsi, ema_fast, ema_slow, macd, macd_signal, macd_hist, atr, adx

    Returns a new DataFrame (does not mutate the input in place).
    """
    out = df.copy()

    rsi = RSIIndicator(close=out["close"], window=config.RSI_PERIOD)
    out["rsi"] = rsi.rsi()

    out["ema_fast"] = EMAIndicator(close=out["close"], window=config.EMA_FAST).ema_indicator()
    out["ema_slow"] = EMAIndicator(close=out["close"], window=config.EMA_SLOW).ema_indicator()

    macd = MACD(
        close=out["close"],
        window_fast=config.MACD_FAST,
        window_slow=config.MACD_SLOW,
        window_sign=config.MACD_SIGNAL,
    )
    out["macd"] = macd.macd()
    out["macd_signal"] = macd.macd_signal()
    out["macd_hist"] = macd.macd_diff()

    atr = AverageTrueRange(high=out["high"], low=out["low"], close=out["close"], window=config.ATR_PERIOD)
    out["atr"] = atr.average_true_range()

    adx = ADXIndicator(high=out["high"], low=out["low"], close=out["close"], window=config.ADX_PERIOD)
    out["adx"] = adx.adx()

    return out.dropna()


def latest_snapshot(df: pd.DataFrame) -> dict:
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
        "adx": round(float(last["adx"]), 2),
    }
