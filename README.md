# Forex Signal Bot

A rule-based forex signal bot with Claude-generated explanations, ATR-based risk
management, and Telegram alerts. Built to run on a GitHub Actions schedule (no server needed),
same pattern as the daily football prediction bot.

**This bot only sends signal alerts. It does not place trades.**

## How it works

1. **Data** (`data_fetcher.py`) — pulls 15-minute OHLC candles for 5 major forex
   pairs via `yfinance` (free, no API key required).
2. **Indicators** (`indicators.py`) — computes RSI, MACD, EMA(12/26), and ATR.
3. **Strategy** (`strategy.py`) — requires 2-of-3 confluence (RSI + MACD flip + EMA trend)
   before firing a BUY/SELL signal. No single indicator can trigger a signal alone.
4. **Risk management** (`risk_manager.py`) — sizes stop-loss and take-profit off ATR
   (volatility-adjusted, not fixed pips), and calculates position size from your
   account balance and risk-per-trade %.
5. **AI reasoning** (`ai_reasoning.py`) — turns the raw indicator numbers into a short
   plain-English explanation of *why* the signal fired. Defaults to **Google Gemini**
   (free, no credit card, ~1,500 requests/day via Google AI Studio). Claude is also
   supported if you'd rather pay for higher-quality reasoning. Falls back to a
   templated explanation if no key is set, the call fails, or you set `AI_PROVIDER=none`.
6. **Telegram alert** (`telegram_notifier.py`) — sends the formatted signal to your
   Telegram chat.
7. **State** (`state_manager.py`) — remembers the last signal per pair in `state.json`
   so you don't get spammed with the same signal every 15 minutes. The GitHub Actions
   workflow commits this file back to the repo after each run.

## Important limitation (read this)

No indicator combination — RSI, MACD, EMA, ATR, or otherwise — eliminates false
signals. This bot reduces noise by requiring multiple conditions to agree, but every
signal is a probabilistic edge, not a guarantee. Treat it as one input among several,
size positions conservatively, and never risk more than you can afford to lose.

## Local setup

```bash
git clone <your-repo>
cd forex_trading_bot
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
export $(cat .env | xargs)   # or use python-dotenv if you prefer
python main.py
```

### Getting a free Gemini API key (default provider)
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with a Google account — no credit card needed
3. Click **Get API key → Create API key**
4. Paste it into `GEMINI_API_KEY` in your `.env`

Set `DRY_RUN=true` in `.env` to test without actually sending Telegram messages —
it'll print what would have been sent instead.

## Website integration (Supabase)

The bot can log every signal it fires into a Supabase table, which the
companion website (`confluence-web`) reads to display public signal history.

1. Create a free Supabase project at supabase.com.
2. In the Supabase dashboard, go to **SQL Editor** and run the contents of
   `confluence-web/supabase/schema.sql` (from the website project) to create
   the `signals` and `profiles` tables.
3. In **Project Settings -> API**, copy:
   - **Project URL** -> `SUPABASE_URL`
   - **service_role key** (NOT the anon key -- this one bypasses row-level
     security so the bot can insert rows) -> `SUPABASE_SERVICE_ROLE_KEY`
4. Add both as GitHub repo secrets (same place as your Telegram secrets).

If these aren't set, the bot still runs exactly as before -- it just skips
the Supabase write and logs a warning. Telegram alerts are never blocked by
a missing or failing Supabase connection.

## Deploying on GitHub Actions

1. Push this repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions** and add:
   - `GEMINI_API_KEY` (free — see above for how to get one)
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `ANTHROPIC_API_KEY` — optional, only needed if you switch `AI_PROVIDER` to `claude`
3. The workflow in `.github/workflows/trading_bot.yml` runs every 15 minutes on its own
   (`cron: "*/15 * * * *"`) and commits `state.json` back to the repo after each run.
4. You can also trigger it manually from the **Actions** tab (`workflow_dispatch`).

Adjust the cron schedule if you change `DATA_INTERVAL` in `config.py` — they should
roughly match, or you'll either miss candles or re-check stale ones.

## Customizing

- **Pairs traded:** edit `FOREX_PAIRS` in `config.py`.
- **Risk per trade:** `RISK_PER_TRADE_PCT` and `ACCOUNT_BALANCE` in `config.py` (or `.env`).
- **Stop/target distance:** `ATR_STOP_MULTIPLIER` / `ATR_TARGET_MULTIPLIER` in `config.py`.
- **Switch AI provider:** set `AI_PROVIDER` in `.env` to `gemini` (free, default), `claude`
  (paid, higher quality), or `none` (skip AI entirely — templated fallback, no API calls made).
- **Swap the data source:** everything in `data_fetcher.py` funnels through `fetch_ohlc()`.
  Replace the yfinance call with OANDA, Twelve Data, or MetaTrader5 without touching
  any other file — the DataFrame contract (`open`, `high`, `low`, `close`, `volume`) stays the same.

## File structure

```
forex_trading_bot/
├── config.py              # all settings and env vars
├── data_fetcher.py         # OHLC data ingestion
├── indicators.py           # RSI, MACD, EMA, ATR
├── strategy.py              # confluence signal logic
├── risk_manager.py         # stop-loss/take-profit/position sizing
├── ai_reasoning.py          # Gemini (free) / Claude (paid) explanation generation
├── telegram_notifier.py    # Telegram formatting + sending
├── state_manager.py        # persists last signal per pair
├── engine.py                # orchestrates the full pipeline
├── main.py                  # entry point
├── requirements.txt
├── .env.example
└── .github/workflows/trading_bot.yml   # scheduled GitHub Actions run
```
