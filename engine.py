import data_fetcher
import indicators
import strategy
import risk_manager
import ai_reasoning
import telegram_notifier
import supabase_logger
import outcome_tracker
import state_manager
import config
from datetime import datetime, timezone


def _in_dead_zone() -> bool:
    if not config.SESSION_FILTER_ENABLED:
        return False
    hour = datetime.now(timezone.utc).hour
    return config.DEAD_ZONE_START_UTC <= hour < config.DEAD_ZONE_END_UTC


def process_pair(pair: str, df, state: dict) -> None:
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

    if new_signal != "HOLD" and _in_dead_zone():
        current_hour = datetime.now(timezone.utc).hour
        print(f"[{pair}] signal={new_signal} suppressed (dead zone, {current_hour}:00 UTC)")
        return

    suppressed_note = f" [{result['suppressed']}]" if result.get("suppressed") else ""
    print(f"[{pair}] signal={new_signal} last={last_signal} rsi={snapshot['rsi']} "
          f"macd_hist={snapshot['macd_hist']} adx={snapshot['adx']}{suppressed_note}")

    if new_signal == "HOLD":
        if last_signal != "HOLD":
            telegram_notifier.send_telegram_message(
                f"\u2139\ufe0f <b>Position Status:</b> {pair.replace('=X', '')} returned to HOLD/neutral state."
            )
            state[pair] = "HOLD"
        return

    if new_signal == last_signal:
        return

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
    print("[ENGINE] Starting forex signal scan...")
    state = state_manager.load_state()

    all_data = data_fetcher.fetch_all_pairs()
    if not all_data:
        print("[ENGINE] No data fetched for any pair this run. Exiting.")
        return

    for pair, df in all_data.items():
        process_pair(pair, df, state)

    outcome_tracker.update_pending_outcomes(all_data)

    state_manager.save_state(state)
    print("[ENGINE] Scan complete.")
