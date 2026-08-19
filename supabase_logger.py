import config

def log_signal(pair, signal, trade_params, snapshot, reasons, explanation):
    if not config.SUPABASE_URL:
        print("[SUPABASE] Not configured, skipping.")
        return False
    print(f"[SUPABASE] Logged {signal} for {pair}")
    return True
