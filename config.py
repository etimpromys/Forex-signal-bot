"""
config.py
Centralized configuration for the Forex Trading Bot.
All secrets are pulled from environment variables (set as GitHub Actions secrets
in production, or a local .env file when running locally).
"""

import os

# --- API Keys / Secrets ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- AI provider for signal explanations ---
# "gemini" -> free (Google AI Studio, no credit card, ~1,500 requests/day)
# "claude" -> paid (Anthropic API, higher quality, costs pennies per explanation)
# "none"   -> skip AI entirely, use the templated fallback explanation
AI_PROVIDER = os.getenv("AI_PROVIDER", "none").lower()

# --- Models used for reasoning/explanation generation ---
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Trading Universe ---
# yfinance ticker format for FX pairs, e.g. EURUSD=X, GBPUSD=X, USDJPY=X
FOREX_PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "USDCHF=X",
    "AUDUSD=X",
]

# --- Data Settings ---
DATA_INTERVAL = os.getenv("DATA_INTERVAL", "15m")   # yfinance interval
DATA_PERIOD = os.getenv("DATA_PERIOD", "5d")         # lookback window (yfinance limits intraday history)

# --- Indicator Parameters ---
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

EMA_FAST = 12
EMA_SLOW = 26

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

ATR_PERIOD = 14

# --- Risk Management ---
ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", "10000"))   # notional, for position sizing math only
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "1.0"))  # % of account risked per trade
ATR_STOP_MULTIPLIER = 1.5     # stop-loss = entry -/+ (ATR * multiplier)
ATR_TARGET_MULTIPLIER = 3.0   # take-profit = entry -/+ (ATR * multiplier) -> ~2:1 reward:risk

# --- State Persistence ---
STATE_FILE = os.getenv("STATE_FILE", "state.json")

# --- Behavior Flags ---
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"  # if true, skip Telegram sends (log only)
