"""
strategy.py
Combines RSI, MACD, and EMA into a confluence-based signal.

Design note (carried over from our earlier discussion): no combination of
indicators eliminates false signals. This strategy requires 2-of-3 conditions
to agree before firing, which reduces noise but does NOT guarantee accuracy.
Treat every signal as a probabilistic edge, not a certainty.

Confluence conditions per direction:
  BUY requires at least 2 of:
    - RSI crossing up from oversold territory (rsi < 40, trending up)
    - MACD histogram flipping positive (bullish momentum shift)
    - EMA fast > EMA slow (trend filter, fast above slow = uptrend)

  SELL requires at least 2 of:
    - RSI crossing down from overbought territory (rsi > 60, trending down)
    - MACD histogram flipping negative (bearish momentum shift)
    - EMA fast < EMA slow (trend filter, fast below slow = downtrend)
"""

from typing import Dict, Any
import config


def evaluate_signal(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes an indicator snapshot (from indicators.latest_snapshot) and returns:
    {
        "signal": "BUY" | "SELL" | "HOLD",
        "confluence_count": int,
        "reasons": [list of str, which conditions fired]
    }
    """
    rsi = snapshot["rsi"]
    macd_hist = snapshot["macd_hist"]
    macd_hist_prev = snapshot["macd_hist_prev"]
    ema_fast = snapshot["ema_fast"]
    ema_slow = snapshot["ema_slow"]

    buy_reasons = []
    sell_reasons = []

    # RSI condition
    if rsi < 40:
        buy_reasons.append(f"RSI at {rsi} is below 40 (oversold zone)")
    if rsi > 60:
        sell_reasons.append(f"RSI at {rsi} is above 60 (overbought zone)")

    # MACD histogram flip
    if macd_hist > 0 and macd_hist_prev <= 0:
        buy_reasons.append("MACD histogram flipped positive (bullish momentum shift)")
    if macd_hist < 0 and macd_hist_prev >= 0:
        sell_reasons.append("MACD histogram flipped negative (bearish momentum shift)")

    # EMA trend filter
    if ema_fast > ema_slow:
        buy_reasons.append(f"EMA{config.EMA_FAST} above EMA{config.EMA_SLOW} (uptrend)")
    if ema_fast < ema_slow:
        sell_reasons.append(f"EMA{config.EMA_FAST} below EMA{config.EMA_SLOW} (downtrend)")

    if len(buy_reasons) >= 2 and len(buy_reasons) > len(sell_reasons):
        return {"signal": "BUY", "confluence_count": len(buy_reasons), "reasons": buy_reasons}

    if len(sell_reasons) >= 2 and len(sell_reasons) > len(buy_reasons):
        return {"signal": "SELL", "confluence_count": len(sell_reasons), "reasons": sell_reasons}

    return {"signal": "HOLD", "confluence_count": 0, "reasons": []}
