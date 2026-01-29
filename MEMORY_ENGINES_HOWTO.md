# Using Memory Engines - Practical Guide

## Quick Start: See Memory Engines in Action

### **1. Start the Project**
```bash
cd /workspaces/quantum-market-observer-/backend
python -m uvicorn api.routes:app --host 0.0.0.0 --port 8000 --reload
```

### **2. Open in Browser**
```
http://localhost:8000
```

### **3. Watch the AI Mentor Panel**
The 5 drawers update every 5 seconds with ALL 11 memories queried:

```
┌─────────────────────────────────────────────────────┐
│                    AI MENTOR PANEL                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🔷 Gann Drawer                                     │
│     Uses: Cycle Memory, Trade Memory               │
│     Shows: Price levels, S/R, angles               │
│     Updates every 5 sec with cycle confirmation    │
│                                                     │
│  🔶 Astro Drawer                                    │
│     Uses: Cycle Memory, time-based patterns        │
│     Shows: Aspects, volatility outlook             │
│     Updates every 5 sec with alignment             │
│                                                     │
│  🧊 Iceberg Drawer ← USES MOST MEMORIES            │
│     Uses: ALL 3 iceberg memories + more            │
│     Shows: Zone price, volume, strength            │
│     Updates with real-time absorption detection    │
│                                                     │
│  📰 News Drawer                                     │
│     Uses: News Memory + upcoming events            │
│     Shows: Calendar, headlines, reactions          │
│     Updates with event risk data                   │
│                                                     │
│  🌍 Global Markets Drawer                           │
│     Uses: Structure Memory + Session Learning      │
│     Shows: Session context, narrative              │
│     Updates with multi-timeframe alignment         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## How to Verify Each Memory is Working

### **Memory #1: Trade Memory**

**Check it's working:**
```bash
# Look at the JSON file
cat trade_memory.json | jq '.stats'

# Should show:
{
  "total_trades": 5,
  "winning_trades": 4,
  "losing_trades": 1,
  "total_pnl": 85.0,
  "win_rate": 0.8,
  "avg_pnl": 17.0
}
```

**How to trigger:**
1. In the AI Panel, record a trade manually
2. Or run tests: `python -m pytest backend/memory/ -k "MemoryEngine" -v`

**Signal of working:**
```
✓ trade_memory.json file exists and grows
✓ stats.total_trades increments
✓ win_rate is calculated correctly
```

---

### **Memory #2-4: Iceberg Memories** (Most important!)

**Check Iceberg Memory (#2):**
```bash
# Look at the JSON file
cat iceberg_memory.json | jq '.[0]'

# Should show:
{
  "instrument": "GC=F",
  "price_low": 3349.5,
  "price_high": 3350.5,
  "session": "LONDON",
  "date": "2026-01-23",
  "side": "BUY_SIDE",
  "volume_strength": 1250,
  "delta_bias": 0.6,
  "reaction_result": "BOUNCE",
  "times_retested": 3
}
```

**Check Absorption Zone Memory (#3) - Real-time:**
```bash
# Make API call
curl -s http://localhost:8000/api/v1/mentor -X POST \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.iceberg_activity'

# Should show:
{
  "detected": true,
  "price_from": 3350,
  "price_to": 3375,
  "volume_spike_ratio": 2.71,
  "delta_direction": "BEARISH",
  "absorption_count": 7
}
```

**Check Iceberg Chain Memory (#4):**
```bash
# This tracks recurring zones
# After 3+ sessions with zone 3350:
# Occurrence count should increase
# Sessions list should show: ["Asia", "London", "NewYork"]

# Verify in tests:
python -m pytest backend/memory/iceberg_chain_memory.py -v
```

---

### **Memory #5: Signal Memory**

**Check it's working:**
```bash
# Make a test call
python3 << 'EOF'
from backend.memory.signal_memory import SignalMemory

mem = SignalMemory()

# Record some signals
mem.store_signal("Iceberg breakout", entry=3350, exit=3365, pnl=15)
mem.store_signal("Iceberg breakout", entry=3350, exit=3340, pnl=-10)
mem.store_signal("Gann rejection", entry=3375, exit=3360, pnl=15)

# Check win rate
print(f"Win rate: {mem.win_rate():.1%}")  # Should be 66.7%
print(f"Signals: {len(mem.signals)}")      # Should be 3
EOF

# Output:
# Win rate: 66.7%
# Signals: 3
```

---

### **Memory #6: Performance Memory**

**Check it's working:**
```bash
# In API response, look for:
curl -s http://localhost:8000/api/v1/mentor -X POST \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.risk_assessment'

# Should show metrics like:
{
  "risk_level": "MEDIUM",
  "recommended_risk_pct": 1.5,
  "max_daily_loss": 24.58,
  "stop_loss": 4951.56,
  "trades_remaining": 4,
  "risk_reward_ratio": 1.8
}
```

---

### **Memory #7: Cycle Memory**

**Check it's working:**
```bash
# Look in mentor response
curl -s http://localhost:8000/api/v1/mentor -X POST \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.context_bullets'

# Should mention cycle status, e.g.:
# "15m: Setup completeness 75% with confluence from volume + price action."
# (confluence score is updated from cycle memory)
```

---

### **Memory #8: Session Learning** ⭐ Most Advanced

**Check it's working:**
```bash
# This is the most sophisticated - takes 20-30 sessions to show effect
# But you can test it directly:

python3 << 'EOF'
from backend.intelligence.session_learning_memory import SessionLearningMemory

mem = SessionLearningMemory()

# Simulate 10 trades in London session
for i in range(7):
    mem.record_result("iceberg", win=True, session="London")
    mem.record_result("gann", win=False, session="London")

# Check what London learned
print("London performance:", mem.session_memory["London"]["setup_performance"])
# Output: iceberg 7 wins, gann 0 wins
# Conclusion: "In London, use icebergs!"
EOF
```

**How it helps:**
```
After 30 days of trading:
London session setup performance:
├─ Iceberg: 71% win rate (24/34 trades)
├─ Gann: 58% win rate (18/31 trades)
└─ Astro: 44% win rate (13/30 trades)

AI learns: "In London hours (7am-4pm), use iceberg setups!"
→ Next time London session arrives, mentor will suggest icebergs first
→ Automatically adaptive strategy
```

---

### **Memory #9: Edge Decay Engine**

**Check it's working:**
```bash
python3 << 'EOF'
from backend.memory.edge_decay_engine import EdgeDecayEngine

edge = EdgeDecayEngine()

# Simulate 10 trades on "iceberg" setup
for i in range(8):
    edge.update("iceberg", win=True)    # 8 wins
for i in range(2):
    edge.update("iceberg", win=False)   # 2 losses

# Check edge strength
strength = edge.edge_strength("iceberg")
print(f"Edge strength: {strength:.2f}")  # Should be 0.80

# Position sizing
position_size = 1.0 * strength
print(f"Position size multiplier: {position_size:.2f}x")  # 0.80x
EOF
```

**Practical use:**
```
Edge strength 0.80 = Be 80% aggressive with this setup
Position size = base × 0.80

As edge improves (more wins):
Edge 0.85 → Position size = base × 0.85
Edge 0.90 → Position size = base × 0.90

As edge degrades (more losses):
Edge 0.45 → Position size = base × 0.45
Edge 0.30 → Filter out this setup (stop using it)
```

---

### **Memory #10: News Memory**

**Check it's working:**
```bash
# In mentor response, look for:
curl -s http://localhost:8000/api/v1/mentor -X POST \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.news_events'

# Should show upcoming events:
[
  {
    "time_utc": "2026-01-23T14:30:00",
    "event_name": "US CPI",
    "importance": "HIGH",
    "impact_xauusd": "BEARISH"
  },
  ...
]

# And major news:
jq '.major_news'
[
  {
    "headline": "Fed Officials Signal Cautious Rate Path",
    "sentiment": "BEARISH",
    "impact": "Moderate downside pressure"
  },
  ...
]
```

---

### **Memory #11: Structure Memory**

**Check it's working:**
```bash
# In mentor response:
curl -s http://localhost:8000/api/v1/mentor -X POST \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.htf_structure'

# Should show:
{
  "trend": "BEARISH",
  "bos": "3388 → 3320",
  "range_high": 3965.8,
  "range_low": 3865.8,
  "equilibrium": 3915.8,
  "bias": "SELL"
}

# This is used to confirm multi-timeframe alignment
# All memories together check if structure aligns with signals
```

---

## Complete Test Suite for Memory Engines

```bash
cd /workspaces/quantum-market-observer-

# Run all memory tests
python -m pytest backend/memory/ -v

# Expected output:
# ✓ test_cycle_memory.py - cycle recording and retrieval
# ✓ test_performance_memory.py - trade metrics recording
# ✓ test_iceberg_chain.py - recurring zone detection
# ✓ test_signal_memory.py - signal win rate calculation
# ✓ test_edge_decay.py - edge strength calculation
# ✓ test_iceberg_memory.py - zone persistence

# Run session learning test (most advanced)
python -m pytest backend/intelligence/test_session_learning.py -v

# Run full integration test
python -m pytest test_step23_first.py -v
```

---

## Live Monitoring: Watch Memories Update

### **Terminal 1: Start backend**
```bash
cd /workspaces/quantum-market-observer-/backend
python -m uvicorn api.routes:app --host 0.0.0.0 --port 8000 --reload
```

### **Terminal 2: Monitor memory files**
```bash
# Watch trade memory update
watch -n 5 'cat trade_memory.json | jq ".stats"'

# Watch iceberg memory grow
watch -n 5 'cat iceberg_memory.json | jq "length"'

# Monitor API responses
watch -n 5 'curl -s http://localhost:8000/api/v1/status | jq ".decision"'
```

### **Terminal 3: Make requests and trigger memories**
```bash
# Get full mentor response (queries all 11 memories)
curl -X POST http://localhost:8000/api/v1/mentor \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.'

# Get just iceberg activity (queries iceberg memories)
curl -X POST http://localhost:8000/api/v1/mentor \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.iceberg_activity'

# Get just confidence score (all memories contribute)
curl -X POST http://localhost:8000/api/v1/mentor \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.confidence_percent'
```

---

## Expected Behavior Over Time

### **Hour 1 (Fresh start)**
```
Trade Memory: 0 trades (no history)
Iceberg Memory: From previous sessions (if any)
Session Learning: Generic defaults
Edge Decay: Neutral (1.0 - unknown)
Confidence: 50-60% (no conviction)
```

### **Hour 4 (After ~30 bars = 2.5 hours of 5m candles)**
```
Trade Memory: 4-5 trades recorded
Iceberg Memory: 2-3 zones detected
Session Learning: Patterns emerging
Edge Decay: Starting to form (3-5 data points)
Confidence: 65-75% (cautious)
```

### **End of Day (50-60 trades recorded)**
```
Trade Memory: 50+ trades, win rate stabilizing
Iceberg Memory: 15-20 zones, success rates calculated
Session Learning: Session preferences clear
Edge Decay: Strong edges identified (0.70+ strength)
Confidence: 80-95% on converged signals (aggressive)
```

### **After 1 Week (300+ trades)**
```
Trade Memory: Reliable win rate (±2%)
Iceberg Memory: Recurring zones identified, robust
Session Learning: Session preferences locked in
Edge Decay: Weak setups filtered out automatically
Confidence: 85-98% on best signal combinations
→ System reaches professional competence
```

---

## Troubleshooting Memory Engines

### **Problem: Memory files not being created**
```bash
# Check permissions
ls -la *.json

# If not created, manually create them:
python3 << 'EOF'
import json
with open('trade_memory.json', 'w') as f:
    json.dump({"trades": [], "stats": {"total_trades": 0, "winning_trades": 0, "losing_trades": 0, "total_pnl": 0}}, f)
with open('iceberg_memory.json', 'w') as f:
    json.dump([], f)
EOF
```

### **Problem: Session Learning shows generic performance**
```
✓ This is normal - it needs 20-30 sessions to show adaptation
✓ After 1 week, you'll see clear session preferences
✓ After 1 month, system will be highly adaptive
```

### **Problem: Confidence not increasing**
```bash
# Check if memories are being updated
python3 << 'EOF'
from backend.memory.edge_decay_engine import EdgeDecayEngine
edge = EdgeDecayEngine()
print("Stats:", edge.stats)  # Should show entries after trades
EOF

# If empty, memories aren't being saved properly
# Check: API response returns memory data correctly?
curl -X POST http://localhost:8000/api/v1/mentor \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GC=F","interval":"5m"}' | jq '.confidence_percent'
```

---

## Key Performance Indicators (KPIs)

Track these metrics over your one-month testing:

```
Daily KPIs:
├─ Trade Memory: Win rate (target >60%)
├─ Iceberg Memory: Zone success rate (target >70%)
├─ Iceberg Chain: Recurring zone count (target >5 by day 5)
├─ Edge Decay: Strongest edge value (target >0.70 by day 10)
├─ Session Learning: Best session win rate (target >65% by week 2)
├─ Confidence avg: Average confidence on executed trades (target >80% by day 15)
└─ P&L: Cumulative P&L (target >500 pips by month end)

Weekly KPIs:
├─ Memory convergence: # of setups with 3+ memory confirmations
├─ Session adaptation: Difference between session performance
├─ Edge stability: Variance in edge strength
├─ False signal rate: Trades where confidence >80% but loss occurred
└─ Learning curve: Improvement in metrics week-over-week
```

---

## Summary: Memory Engines in Your Project

```
11 Memory Engines
    ▼
Collect data from every trade
    ▼
Learn patterns and preferences
    ▼
Calculate confidence scores
    ▼
Generate adaptive predictions
    ▼
Update in real-time (5-second refresh)
    ▼
Display in AI Mentor Panel
    ▼
Use for next trade decision
    ▼
Record outcome (feedback loop)
    ▼
✨ System becomes smarter ✨
```

**The AI Mentor learns like a professional trader learns through experience!**
