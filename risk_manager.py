import config

def calculate_trade_parameters(signal, entry_price, atr, account_balance=None, risk_pct=None):
    account_balance = account_balance or config.ACCOUNT_BALANCE
    risk_pct = risk_pct if risk_pct is not None else config.RISK_PER_TRADE_PCT
    stop_distance = atr * config.ATR_STOP_MULTIPLIER
    target_distance = atr * config.ATR_TARGET_MULTIPLIER
    if signal == "BUY":
        stop_loss = round(entry_price - stop_distance, 5)
        take_profit = round(entry_price + target_distance, 5)
    else:
        stop_loss = round(entry_price + stop_distance, 5)
        take_profit = round(entry_price - target_distance, 5)
    risk_amount = round(account_balance * (risk_pct / 100), 2)
    position_size_units = round(risk_amount / stop_distance, 2) if stop_distance > 0 else 0
    risk_reward_ratio = round(target_distance / stop_distance, 2) if stop_distance > 0 else 0
    return {
        "entry_price": entry_price, "stop_loss": stop_loss, "take_profit": take_profit,
        "risk_amount_usd": risk_amount, "position_size_units": position_size_units,
        "risk_reward_ratio": risk_reward_ratio, "atr_used": round(atr, 5),
    }
