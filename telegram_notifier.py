import config

def send_telegram_message(text):
    print(f"[TELEGRAM] {text}")
    return True

def format_and_send_signal(pair, signal, trade_params, snapshot, explanation):
    print(f"[TELEGRAM] {signal} {pair} entry={trade_params['entry_price']}")
    return True
