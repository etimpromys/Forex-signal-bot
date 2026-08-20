# TradeIQ — Roadmap / Deferred Items

Things we've deliberately decided to revisit later rather than build now,
across all three parts of the project (signal bot, website, MT5 executor).
Nothing here is broken or blocking — these are intentional "not yet"
decisions, kept in one place so they don't get lost.

---

## Website (TradeIQ-Web)

- [ ] **Subscriptions/payments** — pricing page already shows "Pro — coming
      soon." Wire in Paystack or Flutterwave when ready to charge.
- [ ] **Ads** — no ad network integrated yet. Likely a single script tag
      (e.g. Google AdSense) once there's real traffic to monetize.
- [ ] **Password reset flow** — Supabase supports it natively; just never
      wired into the login UI.

## Strategy tuning (data-driven — check evidence before acting)

- [ ] **Hour 14 UTC dip** — showed a real dip (25% win rate) even inside
      the "good" trading window (08:00-15:59 UTC), but only ~8 signals so
      far — too thin to act on. Re-check once that hour has 15-20+
      resolved signals.
- [ ] **ADX filter effectiveness** — added to suppress signals during
      strong-trend days (see Aug 18 dollar-rally incident). Needs a few
      weeks of resolved signals to confirm it's actually helping, not just
      theoretically sound.
- [ ] **Trend-filter / RSI tightening** (mandatory EMA agreement instead of
      2-of-3, and/or tighter RSI thresholds like <30/35 instead of <40) —
      deliberately held back so the session filter's effect could be
      isolated first. Only revisit if the ADX filter's results still leave
      meaningful room for improvement.
- [ ] **Second, trend-following strategy** — bigger, later-stage idea: use
      ADX to switch into a trend-following approach on high-ADX days
      instead of just suppressing signals entirely. Explicitly "not now" —
      only worth building once the ADX suppression filter's value is
      confirmed with real data.

## MT5 execution

- [ ] **Real position sizing** — executor currently uses a fixed lot size
      (0.1) regardless of account balance. Proper ATR/risk-based sizing
      tied to actual MT5 account balance was flagged as a deliberate
      change to make consciously, not silently.
- [ ] **MT5 $ P&L vs. Supabase pip-tracking comparison** — once enough
      auto-executed trades accumulate, compare MT5's real profit/loss
      (includes spread/slippage) against the pip-based numbers Supabase
      tracks, to sanity-check the whole pipeline end-to-end.
- [ ] **Re-entry logic for missed signals** — if the laptop running the
      executor is off when a signal fires, it's currently just skipped
      once older than `MAX_SIGNAL_AGE_MINUTES`, not queued for later.

## Housekeeping (low priority, no rush)

- [ ] **GitHub Actions version bump** (`actions/checkout@v5`,
      `actions/setup-python@v6`) — clears the Node 20 deprecation warning
      in workflow logs. Purely cosmetic, no functional impact.
- [ ] **Nigerian tax implications** on forex profits (Tax Act 2025,
      effective Jan 2026) — worth looking into properly once real money is
      involved. Not something Claude can advise on directly — consult a
      tax professional when the time comes.

---

*Last updated: 20 August 2026. Add new deferred items here as they come up
during future sessions, so context doesn't get lost between conversations.*
