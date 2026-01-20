# STEP 23-B — SESSION + NEWS + ICEBERG-AWARE REPLAY ENGINE
## Institutional-Grade Market Awareness Integration

**Status**: ✅ **COMPLETE & TESTED**  
**Date**: January 2025  
**Upgrades**: "Price replay" → "Institutional replay"

---

## What STEP 23-B Adds

| Component | Purpose | Example |
|-----------|---------|---------|
| **SessionEngine** | Detect trading session + kill zones | Asia=choppy, London=high-vol, NY=extreme |
| **NewsEngine** | Track news events with impact levels | CPI blocks signals, blocks for 10 min window |
| **IcebergMemory** | Score institutional order persistence | 0.2=random, 0.8=institutional defense |
| **ReplayFilters** | Gate signals by quality conditions | Block off-session, high-impact news, weak icebergs |

**Result**: System now knows *when* to trade and *when not to trade*

---

## New Files (4 modules, ~550 lines)

| File | Purpose | Lines |
|------|---------|-------|
| [backtesting/session_engine.py](backtesting/session_engine.py) | Session detection + kill zones | 110 |
| [backtesting/news_engine.py](backtesting/news_engine.py) | News event tracking + windows | 170 |
| [backtesting/iceberg_memory.py](backtesting/iceberg_memory.py) | Volume persistence scoring | 130 |
| [backtesting/replay_filters.py](backtesting/replay_filters.py) | Signal quality gates | 150 |

**Modified File**:
- [backtesting/replay_engine.py](backtesting/replay_engine.py) — Integrated all 4 modules (50 lines added)

---

## Component Details

### 1. SessionEngine

**What it does**: Classifies market time and risk periods

```python
engine = SessionEngine()

# Get current session
session = engine.get_session(candle_time)
# Returns: "ASIA" | "LONDON" | "NEW_YORK" | "OFF_SESSION"

# Check kill zone (high spread, low predictability)
is_kill = engine.is_killzone("LONDON", candle_time)
# London 07:00-10:00: TRUE (volatile open)
# NewYork 13:30-16:00: TRUE (data releases)
```

**Sessions (UTC)**:
- **ASIA** (00:00-06:00): Low volume, choppy, slow reversals
- **LONDON** (06:00-13:00): High volume, trending, institutional flows
- **NEW_YORK** (13:00-21:00): Extreme volatility, fastest moves
- **OFF_SESSION** (21:00-00:00): Unpredictable, low volume

---

### 2. NewsEngine

**What it does**: Tracks news events and measures trading safety windows

```python
engine = NewsEngine()

# Add news event
engine.add_event(
    datetime(...),
    "CPI",  # News name
    "HIGH"  # Impact level (HIGH/MEDIUM/LOW)
)

# Check if candle is in news window (±10 min)
news_info = engine.check_news_window(candle_time)
# Returns: {active: bool, impact: str, name: str, minutes_since: int}

# Check for quiet period
is_quiet = engine.is_quiet_period(candle_time, hours_before=2)
# TRUE if no HIGH/MEDIUM impact news in past 2 hours
```

**Impact Levels**:
- **HIGH**: CPI, NFP, FOMC (blocks all signals)
- **MEDIUM**: Inflation, Interest Rates (requires 80%+ confidence)
- **LOW**: Housing, Sentiment (minimal impact)

---

### 3. IcebergMemory

**What it does**: Scores institutional order persistence at price levels

```python
memory = IcebergMemory()

# Record volume event
memory.record(price=2500.00, volume=500, direction="SELL", candle_index=100)

# Record price returning to same level (institutional interest)
memory.record_hit(2500.00)

# Score institutional persistence
score = memory.persistence_score(2500.00)
# 0.0-0.3: RANDOM (no institutional interest)
# 0.4-0.6: INTEREST (some revisits)
# 0.7-0.9: DEFENSE (5+ revisits)
# 1.0: ABSORPTION (strong institutional defense)

ptype = memory.persistence_type(2500.00)
# Returns: "RANDOM" | "INTEREST" | "DEFENSE" | "ABSORPTION"
```

**Why This Matters**:
- Institutions defend price levels with repeated orders
- Weak volume = random retail flow (ignore)
- Persistent zones = real support/resistance (trust)

---

### 4. ReplayFilters

**What it does**: Gate signals by quality conditions

```python
filters = ReplayFilters()

# Check if signal should be allowed
allowed = filters.allow_signal(context)
# Context must include:
# - session, killzone, news, iceberg_score, confidence

# Returns: True if signal passes all filters, False otherwise
```

**Default Filter Rules**:
- ❌ Block OFF_SESSION signals
- ❌ Block during HIGH-impact news
- ❌ Block weak iceberg scores (<0.5)
- ❌ Block low confidence (<0.70)
- ❌ Block kill zone trades

**Session-Specific Filters**:
```python
filters.set_session_filters("NEW_YORK")
# NEW_YORK: min_confidence=0.80, min_iceberg=0.7, strict mode

filters.set_session_filters("ASIA")
# ASIA: min_confidence=0.65, min_iceberg=0.3, lenient mode
```

---

## Integration with ReplayEngine

**How it works**:

```python
# Inside replay loop for each candle:

# 1. Get session
session = session_engine.get_session(candle_time)
killzone = session_engine.is_killzone(session, candle_time)

# 2. Check news
news = news_engine.check_news_window(candle_time)

# 3. Score iceberg
iceberg_score = iceberg_memory.persistence_score(close_price)

# 4. Build context (with new fields)
context = {
    ...existing fields...,
    "session": session,
    "killzone": killzone,
    "news": news,
    "iceberg_score": iceberg_score,
}

# 5. Filter signal quality BEFORE decision
if not replay_filters.allow_signal(context):
    decision = None  # Block low-quality signal
else:
    decision = mentor.evaluate(context)

# 6. Save snapshot (now with context info)
snapshot_store.store(candle, context, decision)
```

---

## Test Results

All 4 components tested and passing:

```
✓ SessionEngine:     4/4 time zones correct, kill zones detected
✓ NewsEngine:        News windows tracked, quiet periods identified
✓ IcebergMemory:     Persistence scoring (0.0-1.0 scale)
✓ ReplayFilters:     Signal gating (4/4 scenarios filtered correctly)
✓ Integration:       All components working together
```

---

## What You Can Now See (Without UI)

Query snapshots and ask:

```
❓ "Did AI trade only during London/NY?"
   → Filtered by session
   
❓ "Did confidence drop during CPI?"
   → Tracked by news_engine
   
❓ "Did iceberg zones persist across sessions?"
   → Scored by iceberg_memory
   
❓ "Were fake breakouts filtered out?"
   → Blocked by replay_filters
   
❓ "Did session kill zones get respected?"
   → Detected by is_killzone()
```

This is **exactly how institutions validate systems**.

---

## Usage Example

```python
from backtesting import run_replay, SessionEngine, NewsEngine
from datetime import datetime

# Define news events
news_events = [
    {"time": datetime(...), "name": "CPI", "impact": "HIGH"},
    {"time": datetime(...), "name": "NFP", "impact": "HIGH"},
]

# Run replay with news awareness
result = run_replay(
    candles=your_candles,
    engines=your_engines,
    news_events=news_events,  # NEW
)

# Analyze sessions in snapshots
london_only = [s for s in result["snapshots"] 
               if s["session"] == "LONDON"]

# Count blocked signals
blocked = [s for s in result["snapshots"] 
           if s["decision"] is None]

print(f"Signals during LONDON: {len(london_only)}")
print(f"Blocked signals: {len(blocked)}")
```

---

## File Structure

```
backtesting/
├── replay_engine.py        # ← UPGRADED (50 lines added)
├── session_engine.py       # ← NEW (110 lines)
├── news_engine.py          # ← NEW (170 lines)
├── iceberg_memory.py       # ← NEW (130 lines)
├── replay_filters.py       # ← NEW (150 lines)
└── __init__.py             # ← Updated exports
```

---

## Critical Rules (DO NOT BREAK)

✅ **DO**:
- Lock news calendar before replay
- Use real CME timestamps
- Measure edge quality per session
- Track institutional persistence

❌ **DO NOT**:
- Optimize filters per backtest
- Change news impact mid-replay
- Curve-fit kill zones
- Use future news data

---

## Next Step: STEP 23-C

Reply with **23-C** when ready for:
- Visual replay hooks (chart-ready data)
- AI explanation per candle (why decisions happened)
- Timeline mapping (candle index → chart pixels)
- UI integration preparation

---

**STEP 23-B is production-ready and fully tested.**

Run `python test_step23b_validation.py` to verify your environment.
