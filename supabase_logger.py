"""
supabase_logger.py
Writes each fired signal to Supabase so the website's signal history page has
something to read. Uses the service_role key via plain REST calls.

Also stores the full indicator snapshot (RSI, MACD, EMA, ATR, ADX) at the
moment the signal fired, in a jsonb column. This is what lets future filter
ideas be tested against real history in a single SQL query -- e.g. "would a
higher-timeframe trend filter have helped?" -- instead of building the
filter blind, deploying it, and waiting weeks to find out whether the
hypothesis was even right.
"""

import requests
import config


def log_signal(pair: str, signal: str, trade_params: dict, snapshot: dict, reasons: list, explanation: str) -> bool:
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
        # Full indicator state at signal time -- RSI, MACD, EMA, ATR, ADX,
        # whatever indicators.latest_snapshot() currently returns. Stored as
        # jsonb so new indicators can be added later without a schema
        # migration each time.
        "indicator_snapshot": snapshot,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        print(f"[SUPABASE] Logged {signal} signal for {pair} (with indicator snapshot)")
        return True
    except Exception as e:
        print(f"[SUPABASE ERROR] Failed to log signal for {pair}: {e}")
        return False
