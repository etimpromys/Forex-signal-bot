"""
outcome_tracker.py
Checks every 'pending' signal in Supabase against actual price history to
determine whether it hit its stop-loss or take-profit -- and updates the
outcome accordingly. Without this, "outcome" would only ever be manually set
or stay 'pending' forever, even though the indicators cooling back to HOLD
tells you nothing about whether the trade actually won or lost.

Runs using the same OHLC data the engine already fetched this cycle -- no
extra API calls needed. A signal only gets checked on runs where its pair's
data was successfully fetched (i.e. not stale/market-closed).
"""

import requests
from datetime import datetime, timezone
import pandas as pd
import config


def _pip_size(pair: str) -> float:
    """JPY pairs quote 2 decimal places; everything else here quotes 4."""
    return 0.01 if "JPY" in pair else 0.0001


def _headers():
    return {
        "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def fetch_pending_signals():
    """Returns the list of signal rows currently marked outcome='pending'."""
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
        return []

    url = f"{config.SUPABASE_URL}/rest/v1/signals"
    params = {"outcome": "eq.pending", "select": "*"}

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[OUTCOME ERROR] Failed to fetch pending signals: {e}")
        return []


def _update_signal(signal_id: str, outcome: str, pips_result: float = None) -> bool:
    url = f"{config.SUPABASE_URL}/rest/v1/signals"
    params = {"id": f"eq.{signal_id}"}
    payload = {
        "outcome": outcome,
        "closed_at": datetime.now(timezone.utc).isoformat(),
    }
    if pips_result is not None:
        payload["pips_result"] = round(pips_result, 1)

    try:
        resp = requests.patch(url, headers=_headers(), params=params, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[OUTCOME ERROR] Failed to update signal {signal_id}: {e}")
        return False


def _check_signal_against_data(signal: dict, df: pd.DataFrame):
    """
    Walks candles chronologically after the signal's created_at, checking
    whether stop-loss or take-profit was touched first.

    Returns (outcome, exit_price) if resolved, or (None, None) if the price
    hasn't reached either level yet within the data we have.
    """
    created_at = pd.to_datetime(signal["created_at"], utc=True)
    relevant = df[df.index > created_at]

    if relevant.empty:
        return None, None

    signal_type = signal["signal_type"]
    stop_loss = float(signal["stop_loss"])
    take_profit = float(signal["take_profit"])

    for _, candle in relevant.iterrows():
        high = candle["high"]
        low = candle["low"]

        if signal_type == "BUY":
            hit_stop = low <= stop_loss
            hit_target = high >= take_profit
        else:  # SELL
            hit_stop = high >= stop_loss
            hit_target = low <= take_profit

        # If a single candle's range spans both levels, we can't tell from
        # OHLC data alone which was touched first -- assume the stop, since
        # that's the conservative (not overly favorable) assumption.
        if hit_stop:
            return "loss", stop_loss
        if hit_target:
            return "win", take_profit

    return None, None


def update_pending_outcomes(all_data: dict) -> None:
    """
    Checks every pending signal against this run's fetched price data
    (all_data: {pair: DataFrame}, same dict engine.py already built).
    Resolves any that hit stop/target, and expires any that have gone stale
    without resolving within config.OUTCOME_EXPIRE_HOURS.
    """
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
        return

    pending = fetch_pending_signals()
    if not pending:
        return

    now = datetime.now(timezone.utc)

    for signal in pending:
        pair = signal["pair"]
        df = all_data.get(pair)

        if df is None:
            # No fresh data for this pair this run -- try again next run.
            continue

        outcome, exit_price = _check_signal_against_data(signal, df)

        if outcome:
            entry_price = float(signal["entry_price"])
            pip_size = _pip_size(pair)
            if signal["signal_type"] == "BUY":
                pips = (exit_price - entry_price) / pip_size
            else:
                pips = (entry_price - exit_price) / pip_size

            if _update_signal(signal["id"], outcome, pips):
                print(f"[OUTCOME] {pair} {signal['signal_type']} resolved as {outcome.upper()} ({pips:+.1f} pips)")
            continue

        created_at = pd.to_datetime(signal["created_at"], utc=True)
        age_hours = (now - created_at).total_seconds() / 3600
        if age_hours > config.OUTCOME_EXPIRE_HOURS:
            if _update_signal(signal["id"], "expired"):
                print(f"[OUTCOME] {pair} {signal['signal_type']} expired after {config.OUTCOME_EXPIRE_HOURS}h without resolution")
