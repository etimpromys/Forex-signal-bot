"""
risk_manager.py
Calculates stop-loss, take-profit, and position size for a given trade signal,
using ATR (volatility) to size stops rather than a fixed pip count.
"""

from typing import Dict, Any
import config


def calculate_trade_parameters(
    signal: str,
    entry_price: float,
    atr: float,
    account_balance: float = None,
    risk_pct: float = None,
) -> Dict[str, Any]:
    """
    Args:
        signal: "BUY" or "SELL"
        entry_price: current close price
        atr: current ATR value for the pair
        account_balance: notional account size (defaults to config.ACCOUNT_BALANCE)
        risk_pct: % of account risked on this trade (defaults to config.RISK_PER_TRADE_PCT)

    Returns dict with stop_loss, take_profit, risk_amount, position_size_units, risk_reward_ratio.
    """
    account_balance = account_balance or config.ACCOUNT_BALANCE
    risk_pct = risk_pct if risk_pct is not None else config.RISK_PER_TRADE_PCT

    stop_distance = atr * config.ATR_STOP_MULTIPLIER
    target_distance = atr * config.ATR_TARGET_MULTIPLIER

    if signal == "BUY":
        stop_loss = round(entry_price - stop_distance, 5)
        take_profit = round(entry_price + target_distance, 5)
    elif signal == "SELL":
        stop_loss = round(entry_price + stop_distance, 5)
        take_profit = round(entry_price - target_distance, 5)
    else:
        return {"error": "No position sizing for HOLD signal"}

    risk_amount = round(account_balance * (risk_pct / 100), 2)

    # Position size in "units" of base currency, assuming stop_distance is in price terms.
    # For standard lot conversion, divide by pip value separately in a live execution layer.
    position_size_units = round(risk_amount / stop_distance, 2) if stop_distance > 0 else 0

    risk_reward_ratio = round(target_distance / stop_distance, 2) if stop_distance > 0 else 0

    return {
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_amount_usd": risk_amount,
        "position_size_units": position_size_units,
        "risk_reward_ratio": risk_reward_ratio,
        "atr_used": round(atr, 5),
    }
