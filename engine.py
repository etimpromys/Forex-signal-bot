"""
engine.py
Orchestrates one full pass across all configured forex pairs:
fetch data -> compute indicators -> evaluate strategy -> if signal changed,
calculate risk parameters, get Claude's explanation, and alert via Telegram.

Designed to run ONCE per invocation (not an infinite loop), so it fits a
GitHub Actions cron schedule cleanly -- same pattern as the football bot.
"""

import data_fetcher
import indicators
import strategy
import risk_manager
import ai_reasoning
import telegram_notifier
import supabase_logger
import state_manager
import config


def process_pair(pair: str, df, state: dict) -> None:
    """Runs the full pipeline for a single pair and updates state in place."""
    try:
        df_with_indicators = indicators.add_indicators(df)
    except Exception as e:
        print(f"[ENGINE ERROR] Indicator calc failed for {pair}: {e}")
        return

    if df_with_indicators.empty:
        print(f"[ENGINE SKIP] {pair} has no valid rows after indicator calc")
        return

    snapshot = indicators.latest_snapshot(df_with_indicators)
    result = strategy.evaluate_signal(snapshot)
    new_signal = result["signal"]
    last_signal = state.get(pair, "HOLD")

    print(f"[{pair}] signal={new_signal} last={last_signal} rsi={snapshot['rsi']} macd_hist={snapshot['macd_hist']}")

    if new_signal == "HOLD":
        if last_signal != "HOLD":
            telegram_notifier.send_telegram_message(
                f"ℹ️ <b>Position Status:</b> {pair.replace('=X', '')} returned to HOLD/neutral state."
            )
            state[pair] = "HOLD"
        return

    if new_signal == last_signal:
        # Same signal as last run, don't spam another alert
        return

    # New/changed signal -> build the full alert
    trade_params = risk_manager.calculate_trade_parameters(
        signal=new_signal,
        entry_price=snapshot["close"],
        atr=snapshot["atr"],
    )

    explanation = ai_reasoning.generate_explanation(
        pair=pair,
        signal=new_signal,
        snapshot=snapshot,
        strategy_reasons=result["reasons"],
        trade_params=trade_params,
    )

    delivered = telegram_notifier.format_and_send_signal(
        pair=pair,
        signal=new_signal,
        trade_params=trade_params,
        snapshot=snapshot,
        explanation=explanation,
    )

    # Log to the website's signal history regardless of Telegram outcome --
    # the site should reflect what the engine decided even if Telegram is
    # briefly down. State only advances once Telegram delivery succeeds, same
    # as before, so a failed Telegram send will still retry next run.
    supabase_logger.log_signal(
        pair=pair,
        signal=new_signal,
        trade_params=trade_params,
        snapshot=snapshot,
        reasons=result["reasons"],
        explanation=explanation,
    )

    if delivered:
        state[pair] = new_signal


def run_once() -> None:
    """Single full pass across all pairs. Entry point for scheduled runs."""
    print("[ENGINE] Starting forex signal scan...")
    state = state_manager.load_state()

    all_data = data_fetcher.fetch_all_pairs()
    if not all_data:
        print("[ENGINE] No data fetched for any pair this run. Exiting.")
        return

    for pair, df in all_data.items():
        process_pair(pair, df, state)

    state_manager.save_state(state)
    print("[ENGINE] Scan complete.")
