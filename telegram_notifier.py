"""
telegram_notifier.py
Sends formatted trade signal alerts and system status messages to Telegram.
"""

import requests
import config


def send_telegram_message(text: str) -> bool:
    if config.DRY_RUN:
        print(f"[DRY RUN] Would send Telegram message:\n{text}\n")
        return True

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[TELEGRAM ERROR] Missing bot token or chat ID, skipping send.")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[TELEGRAM ERROR] Failed to send message: {e}")
        return False


def format_and_send_signal(
    pair: str,
    signal: str,
    trade_params: dict,
    snapshot: dict,
    explanation: str,
) -> bool:
    emoji = "🟢" if signal == "BUY" else "🔴"

    message = (
        f"{emoji} <b>{signal} SIGNAL — {pair.replace('=X', '')}</b>\n\n"
        f"<b>Entry:</b> {trade_params['entry_price']}\n"
        f"<b>Stop Loss:</b> {trade_params['stop_loss']}\n"
        f"<b>Take Profit:</b> {trade_params['take_profit']}\n"
        f"<b>Risk:Reward:</b> 1:{trade_params['risk_reward_ratio']}\n"
        f"<b>Position Size:</b> {trade_params['position_size_units']} units "
        f"(risking ${trade_params['risk_amount_usd']})\n\n"
        f"<b>Indicators:</b>\n"
        f"  RSI: {snapshot['rsi']} | ATR: {snapshot['atr']} | ADX: {snapshot.get('adx', 'n/a')}\n"
        f"  MACD Hist: {snapshot['macd_hist']} | EMA{config.EMA_FAST}/{config.EMA_SLOW}: {snapshot['ema_fast']}/{snapshot['ema_slow']}\n\n"
        f"<b>Why:</b> {explanation}"
    )

    return send_telegram_message(message)
