"""
backtest_htf_filter.py
Retroactively tests the higher-timeframe (1-hour) trend filter hypothesis
against your EXISTING resolved signal history, without needing to deploy
anything or wait weeks for new data.

How it works:
1. Pulls every resolved (win/loss) signal from Supabase
2. Fetches 1-hour historical price data for each pair, covering the full
   date range your signals span
3. Computes a 1H EMA(50) trend (bullish if price > EMA50, bearish if below)
   for every 1-hour candle
4. For each signal, finds the 1H trend that was active at the exact moment
   it fired
5. Splits your existing win/loss results into "aligned with 1H trend" vs
   "counter-trend" and compares win rate and net pips between the two

If aligned signals clearly outperformed counter-trend ones in your actual
history, that's real evidence the HTF filter would help. If there's no
meaningful difference, that's real evidence it wouldn't -- either way,
you'll know before writing a single line of filter code.

Designed to run as a one-off GitHub Actions job in your existing bot repo --
reuses the SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY secrets already
configured there, and the yfinance/requests/ta dependencies already in
requirements.txt. No local machine needed.

Can also be run locally if preferred:
    pip install pandas yfinance ta requests
    SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python backtest_htf_filter.py
"""

import os
import requests
import pandas as pd
from ta.trend import EMAIndicator

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

HTF_INTERVAL = "1h"
HTF_EMA_PERIOD = 50
HTF_LOOKBACK_PERIOD = "3mo"  # covers the full signal history with margin


def fetch_resolved_signals() -> pd.DataFrame:
    """Pulls every win/loss signal from Supabase."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set in environment")

    url = f"{SUPABASE_URL}/rest/v1/signals"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    params = {
        "outcome": "in.(win,loss)",
        "select": "id,pair,signal_type,created_at,outcome,pips_result",
        "order": "created_at.asc",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    return df


def fetch_htf_trend_series(pair: str) -> pd.DataFrame:
    """
    Fetches 1-hour OHLC data for a pair and computes EMA(50) trend per bar.
    Returns a DataFrame indexed by timestamp with a 'trend' column:
    'bullish' or 'bearish'.
    """
    import yfinance as yf

    df = yf.download(
        tickers=pair,
        interval=HTF_INTERVAL,
        period=HTF_LOOKBACK_PERIOD,
        progress=False,
        auto_adjust=False,
    )

    if df is None or df.empty:
        print(f"  [WARNING] No 1H data returned for {pair}")
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    ema = EMAIndicator(close=df["close"], window=HTF_EMA_PERIOD).ema_indicator()
    df["ema50"] = ema
    df["trend"] = df.apply(
        lambda row: "bullish" if row["close"] > row["ema50"] else "bearish", axis=1
    )

    return df.dropna(subset=["ema50"])


def find_trend_at_time(htf_df: pd.DataFrame, timestamp) -> str | None:
    """Finds the most recent 1H candle at or before the given timestamp, returns its trend."""
    if htf_df.empty:
        return None
    prior = htf_df[htf_df.index <= timestamp]
    if prior.empty:
        return None
    return prior.iloc[-1]["trend"]


def run_backtest():
    print("Fetching resolved signals from Supabase...")
    signals = fetch_resolved_signals()
    print(f"Found {len(signals)} resolved signals.\n")

    pairs = signals["pair"].unique()
    htf_data = {}
    for pair in pairs:
        print(f"Fetching 1H data for {pair}...")
        htf_data[pair] = fetch_htf_trend_series(pair)

    print()
    print("Matching each signal to the 1H trend active at the time it fired...\n")

    results = []
    skipped = 0

    for _, sig in signals.iterrows():
        htf_df = htf_data.get(sig["pair"])
        if htf_df is None or htf_df.empty:
            skipped += 1
            continue

        trend = find_trend_at_time(htf_df, sig["created_at"])
        if trend is None:
            skipped += 1
            continue

        aligned = (sig["signal_type"] == "BUY" and trend == "bullish") or (
            sig["signal_type"] == "SELL" and trend == "bearish"
        )

        results.append(
            {
                "pair": sig["pair"],
                "signal_type": sig["signal_type"],
                "outcome": sig["outcome"],
                "pips_result": sig["pips_result"],
                "htf_trend": trend,
                "aligned": aligned,
            }
        )

    results_df = pd.DataFrame(results)

    if skipped:
        print(f"Skipped {skipped} signals (no 1H data available at that time -- usually the earliest few).\n")

    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    for group_name, group_df in [("ALIGNED with 1H trend", results_df[results_df["aligned"]]),
                                   ("COUNTER to 1H trend", results_df[~results_df["aligned"]])]:
        wins = (group_df["outcome"] == "win").sum()
        losses = (group_df["outcome"] == "loss").sum()
        total = wins + losses
        win_rate = (wins / total * 100) if total else 0
        net_pips = group_df["pips_result"].sum()

        print(f"\n{group_name}:")
        print(f"  {wins}W / {losses}L  ({win_rate:.1f}% win rate)")
        print(f"  Net pips: {net_pips:+.1f}")

    print()
    print("=" * 60)
    print("If ALIGNED meaningfully outperforms COUNTER, that's real evidence")
    print("the HTF filter would help. If they're similar, it likely wouldn't --")
    print("either way, now you know before writing any filter code.")
    print("=" * 60)

    results_df.to_csv("htf_backtest_results.csv", index=False)
    print("\nFull results saved to htf_backtest_results.csv")


if __name__ == "__main__":
    run_backtest()
