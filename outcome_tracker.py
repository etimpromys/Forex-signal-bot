import config

def update_pending_outcomes(all_data):
    if not config.SUPABASE_URL:
        return
    print("[OUTCOME] Checked pending outcomes (stub)")
