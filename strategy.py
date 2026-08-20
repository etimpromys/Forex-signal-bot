"""
strategy.py
Combines RSI, MACD, and EMA into a confluence-based signal, with an ADX
trend-strength filter that suppresses signals during strong-trend
conditions -- see config.py for why.
"""

from typing import Dict, Any
import config


def evaluate_signal(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    rsi = snapshot["rsi"]
    macd_hist = snapshot["macd_hist"]
    macd_hist_prev = snapshot["macd_hist_prev"]
    ema_fast = snapshot["ema_fast"]
    ema_slow = snapshot["ema_slow"]
    adx = snapshot.get("adx")

    if config.ADX_FILTER_ENABLED and adx is not None and adx >= config.ADX_TREND_THRESHOLD:
        return {
            "signal": "HOLD",
            "confluence_count": 0,
            "reasons": [],
            "suppressed": f"ADX {adx} >= {config.ADX_TREND_THRESHOLD} (strong trend, mean-reversion signals unreliable)",
        }

    buy_reasons = []
    sell_reasons = []

    if rsi < 40:
        buy_reasons.append(f"RSI at {rsi} is below 40 (oversold zone)")
    if rsi > 60:
        sell_reasons.append(f"RSI at {rsi} is above 60 (overbought zone)")

    if macd_hist > 0 and macd_hist_prev <= 0:
        buy_reasons.append("MACD histogram flipped positive (bullish momentum shift)")
    if macd_hist < 0 and macd_hist_prev >= 0:
        sell_reasons.append("MACD histogram flipped negative (bearish momentum shift)")

    if ema_fast > ema_slow:
        buy_reasons.append(f"EMA{config.EMA_FAST} above EMA{config.EMA_SLOW} (uptrend)")
    if ema_fast < ema_slow:
        sell_reasons.append(f"EMA{config.EMA_FAST} below EMA{config.EMA_SLOW} (downtrend)")

    if len(buy_reasons) >= 2 and len(buy_reasons) > len(sell_reasons):
        return {"signal": "BUY", "confluence_count": len(buy_reasons), "reasons": buy_reasons}

    if len(sell_reasons) >= 2 and len(sell_reasons) > len(buy_reasons):
        return {"signal": "SELL", "confluence_count": len(sell_reasons), "reasons": sell_reasons}

    return {"signal": "HOLD", "confluence_count": 0, "reasons": []}
