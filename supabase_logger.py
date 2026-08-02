"""
supabase_logger.py
Writes each fired signal to Supabase so the website's signal history page has
something to read. Uses the service_role key (server-side only, never exposed
to the browser/website) via plain REST calls -- no supabase-py dependency needed.

If Supabase isn't configured (keys missing), this fails silently and logs a
warning -- it should never be the reason the bot itself crashes or fails to
send a Telegram alert.
"""

import requests
import config


def log_signal(pair: str, signal: str, trade_params: dict, snapshot: dict, reasons: list, explanation: str) -> bool:
    """
    Inserts one row into the `signals` table.
    Returns True if the insert succeeded, False otherwise (never raises).
    """
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
        print("[SUPABASE] Not configured, skipping signal log (site history won't include this one).")
        return False

    url = f"{config.SUPABASE_URL}/rest/v1/signals"
    headers = {
        "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    payload = {
        "pair": pair,
        "signal_type": signal,
        "entry_price": trade_params["entry_price"],
        "stop_loss": trade_params["stop_loss"],
        "take_profit": trade_params["take_profit"],
        "risk_reward_ratio": trade_params.get("risk_reward_ratio"),
        "confluence_reasons": reasons,
        "explanation": explanation,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        print(f"[SUPABASE] Logged {signal} signal for {pair}")
        return True
    except Exception as e:
        print(f"[SUPABASE ERROR] Failed to log signal for {pair}: {e}")
        return False
