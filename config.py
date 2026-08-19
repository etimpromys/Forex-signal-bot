import os

# --- API Keys / Secrets ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
AI_PROVIDER = os.getenv("AI_PROVIDER", "none").lower()

FOREX_PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "USDCHF=X",
    "AUDUSD=X",
]

DATA_INTERVAL = os.getenv("DATA_INTERVAL", "15m")
DATA_PERIOD = os.getenv("DATA_PERIOD", "5d")
MAX_DATA_AGE_MINUTES = int(os.getenv("MAX_DATA_AGE_MINUTES", "90"))

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

EMA_FAST = 12
EMA_SLOW = 26

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

ATR_PERIOD = 14

ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", "10000"))
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "1.0"))
ATR_STOP_MULTIPLIER = 1.5
ATR_TARGET_MULTIPLIER = 3.0

STATE_FILE = os.getenv("STATE_FILE", "state.json")

# --- Supabase (powers the website's public signal history) ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# --- Outcome tracking ---
OUTCOME_EXPIRE_HOURS = int(os.getenv("OUTCOME_EXPIRE_HOURS", "72"))

# --- Session filter ---
# Evidence-based, from analyzing ~65 resolved signals by UTC hour: win rate
# during 00:00-07:59 UTC (late Asian session, before London liquidity) was
# ~11% across all pairs, vs ~43% during 08:00-15:59 UTC.
SESSION_FILTER_ENABLED = os.getenv("SESSION_FILTER_ENABLED", "true").lower() == "true"
DEAD_ZONE_START_UTC = int(os.getenv("DEAD_ZONE_START_UTC", "0"))
DEAD_ZONE_END_UTC = int(os.getenv("DEAD_ZONE_END_UTC", "8"))

# --- ADX trend-strength filter ---
# ADX measures trend strength, not direction. RSI/MACD/EMA confluence is a
# mean-reversion approach -- it looks for reversals, which works well in
# ranging/choppy markets but gets run over during strong, one-directional
# trend days (e.g. broad risk-off moves where the dollar rallies across
# every major at once). High ADX signals exactly that condition. When
# enabled, new signals are suppressed above the threshold -- existing open
# signals and outcome tracking are unaffected, same pattern as the session
# filter.
ADX_FILTER_ENABLED = os.getenv("ADX_FILTER_ENABLED", "true").lower() == "true"
ADX_PERIOD = int(os.getenv("ADX_PERIOD", "14"))
ADX_TREND_THRESHOLD = float(os.getenv("ADX_TREND_THRESHOLD", "25"))

USE_CLAUDE_REASONING = os.getenv("USE_CLAUDE_REASONING", "false").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
