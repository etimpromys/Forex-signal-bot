import config

def generate_explanation(pair, signal, snapshot, strategy_reasons, trade_params):
    reasons_str = "; ".join(strategy_reasons) if strategy_reasons else "multiple indicator conditions aligned"
    return f"{signal} signal triggered because: {reasons_str}."
