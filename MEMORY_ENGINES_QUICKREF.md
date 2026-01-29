# Memory Engines Quick Reference

## At a Glance: All 11 Memory Engines

### **1️⃣ Trade Memory** 
- **File:** `backend/memory_engine.py`
- **Tracks:** Every trade executed (entry, exit, PnL)
- **Calculates:** Win rate, total P&L, average pips
- **Used for:** Overall performance baseline
- **Example:** "72% win rate on 18 trades = strong system"

---

### **2️⃣ Iceberg Memory Engine**
- **File:** `backend/memory/iceberg_memory.py`
- **Tracks:** Historical iceberg zones (price, volume, session, retests)
- **Persists:** To `iceberg_memory.json`
- **Used for:** Identifying recurring liquidity zones
- **Example:** "Zone 3350 retested 12 times, 71% success rate"

---

### **3️⃣ Absorption Zone Memory**
- **File:** `backend/intelligence/advanced_iceberg_engine.py` (line 279)
- **Tracks:** REAL-TIME absorption zones (BUY vs SELL side)
- **Calculates:** Confidence, proximity scores, institutional pairs
- **Used for:** Live signal generation, activity estimation
- **Example:** "BUY iceberg @3350 (85% confidence), SELL @3375 (92% conf) → range = 25 pips"

---

### **4️⃣ Iceberg Chain Memory**
- **File:** `backend/memory/iceberg_chain_memory.py`
- **Tracks:** Recurring zones as "chains" (same zone appearing repeatedly)
- **Identifies:** Pattern strength and session popularity
- **Used for:** Finding institutional strongholds
- **Example:** "Zone 3350: 12 occurrences, appears in all sessions → VERY RELIABLE"

---

### **5️⃣ Signal Memory**
- **File:** `backend/memory/signal_memory.py`
- **Tracks:** Every signal generated + its outcome
- **Calculates:** Signal win rate per signal type
- **Used for:** Setup validation and confidence scoring
- **Example:** "'Iceberg breakout' signal: 32/50 wins (64% win rate)"

---

### **6️⃣ Performance Memory**
- **File:** `backend/memory/performance_memory.py`
- **Tracks:** Detailed trade metrics (MAE, MFE, R:R, context)
- **Calculates:** Average R:R ratio, MAE/MFE per setup
- **Used for:** Position sizing and risk management
- **Example:** "Iceberg setups: avg +38 pips MFE, avg -14 pips MAE → 2.7:1 R:R"

---

### **7️⃣ Cycle Memory**
- **File:** `backend/memory/cycle_memory.py`
- **Tracks:** Identified cycles (90-bar, 45-bar, 180-bar, etc.)
- **Returns:** Active cycles at current bar count
- **Used for:** Timing confirmations and volatility predictions
- **Example:** "90-bar cycle inflects in 23 bars → expect volatility spike"

---

### **8️⃣ Session Learning Memory** ⭐ (Most Advanced)
- **File:** `backend/intelligence/session_learning_memory.py`
- **Learns:** Which setups work best in each session (Asia/London/NY)
- **Tracks:** Setup performance per session and time-of-day
- **Adapts:** After 20-30 sessions
- **Used for:** Session-specific strategy selection
- **Example:** "London: Iceberg 71%, Gann 58%, Astro 42% → Use icebergs in London!"

---

### **9️⃣ Edge Decay Engine**
- **File:** `backend/memory/edge_decay_engine.py`
- **Tracks:** Win/loss for each setup type
- **Calculates:** Edge strength (0.0 = dead, 1.0 = unknown/neutral, >0.5 = strong)
- **Minimum:** Requires 5 trades before trusting edge
- **Used for:** Position sizing multiplier
- **Example:** "Iceberg setup: 16 wins/21 trades → 76% → Position size = base × 0.76"

---

### **🔟 News Memory**
- **File:** `backend/news/news_memory.py`
- **Tracks:** Economic events and market reactions
- **Learns:** How specific events impact XAUUSD
- **Returns:** Similar past events and outcomes
- **Used for:** Event risk management and volatility estimation
- **Example:** "CPI history: avg -35 pips reaction, 65 pip range → expect similar today"

---

### **1️⃣1️⃣ Structure Memory**
- **File:** `backend/structure/structure_memory.py`
- **Tracks:** Market structure (trends, breaks-of-structure)
- **Stores:** Per-timeframe structure (daily, 4H, 1H)
- **Used for:** Multi-timeframe confluence and bias confirmation
- **Example:** "Daily DOWN, 4H DOWN, 1H DOWN → All aligned bearish → HIGH confidence"

---

## Memory Access in Code

### **In API routes** (`backend/api/routes.py`):
```python
# Line 66: Create real-time absorption memory
absorption_memory = AbsorptionZoneMemory()

# Line 815: Record zone when detected
absorption_memory.record(zone)

# Line 909: Query zones in /mentor endpoint
absorption_zones = list(absorption_memory.zones.values())[:3]
```

### **In Frontend** (`frontend/chart.v4.js`):
```javascript
// Line 195-269: fetchData() pulls all memory data
const response = await fetch('/api/v1/mentor', {...});
const mentor_data = response.json();

// Lines 760-870: setupIcebergDrawer() displays iceberg memory
displayIcebergHistory(mentor_data.iceberg_activity);

// Lines 904-962: setupGlobalMarketsDrawer() uses session context
displaySessionAdaptiveNarrative(mentor_data.session);
```

---

## Memory Flow Summary

```
New trade or market event
        ▼
    Detected
        ▼
    Stored in memories (1-11)
        ▼
    Queried by Mentor Brain
        ▼
    Confidence calculated
        ▼
    Decision generated
        ▼
    Displayed in AI Panel (5 drawers)
        ▼
    Executed or skipped
        ▼
    Outcome recorded
        ▼
    All memories updated
        ▼
    System becomes SMARTER
```

---

## What Each Memory Powers

| Drawer | Memory Engines Used |
|--------|-----|
| **Gann Drawer** | Cycle Memory, Trade Memory |
| **Astro Drawer** | Cycle Memory, Time patterns |
| **Iceberg Drawer** | ALL 3 iceberg memories + Signal memory |
| **News Drawer** | News Memory + upcoming event data |
| **Global Markets** | Structure Memory + Session Learning |

---

## Confidence Score Breakdown

When Mentor decides to trade, it weighs memories:

```
Total Confidence = 
    Trade Memory (15%)              → 72% win rate
  + Iceberg Memories (20%)          → 71% zone success  
  + Session Learning (25%)          → 72% this session
  + Edge Decay (20%)                → 76% edge strength
  + Cycle Memory (15%)              → 85% cycle alignment
  + Structure Memory (5%)           → 90% confluence
  ─────────────────────────────────
  = 94% FINAL CONFIDENCE ✅ EXECUTE

Below 75% = WAIT
75-85% = CAUTIOUS
Above 85% = AGGRESSIVE
```

---

## Data Persistence

### Real-Time (RAM)
- Absorption Zone Memory → Updated every tick
- Cycle Memory → Updated every new bar
- Session Learning → Updated every trade
- Edge Decay → Updated every signal

### Saved to Disk
- Trade Memory → `trade_memory.json`
- Iceberg Memory → `iceberg_memory.json`

### Backed by API
- Session context → `/api/v1/mentor` response
- News events → populated in mentor response
- Global markets → populated in mentor response

---

## Testing Commands

```bash
# See all memories working
cd /workspaces/quantum-market-observer-

# 1. Unit test memories
python -m pytest backend/memory/ -v

# 2. Integration test (Session Learning)
python -m pytest test_step22.py::TestSessionLearningMemory -v

# 3. End-to-end test (all memories)
python -m pytest test_step23_first.py -v

# 4. Check memory files
ls -la *.json
cat iceberg_memory.json | jq '.[0]'    # First zone
cat trade_memory.json | jq '.stats'    # Overall stats

# 5. Live API test (in browser)
# Open: http://localhost:8000/
# Watch: All 5 drawers update every 5 seconds
# Each update = All 11 memories queried
```

---

## Key Insights

### ✅ **Why Multiple Memories?**
- Single metric = unreliable (lucky streak vs real edge)
- Multiple memories = robust (confirmed from many angles)
- Example: 72% iceberg win rate + 71% zone success + 76% edge + London session = 95% confidence

### ✅ **Session Adaptation**
- After 20-30 trades, AI learns session preferences
- Asia = breakouts work better
- London = absorption zones most reliable
- NY = volatility spikes after open
- Result: Mentor suggests different setups per session

### ✅ **Edge Decay**
- Weak edges eliminated after 5 trades
- Edge strengthens with more data
- Position sizing automatically increases with edge confidence
- Prevents over-trading weak patterns

### ✅ **Learning Loop**
```
Each trade →
  ├─ Win/loss recorded in 6 memories
  ├─ Win rates updated
  ├─ Edge strength recalculated
  ├─ Session performance refined
  └─ Next trade = MORE CONFIDENT
```

---

## Real-World Example: 24-Hour Evolution

### **Start of Day** (Limited data)
- Iceberg memory: 50 zones (previous sessions)
- Edge decay: Average edge strength 0.65
- Session learning: Last session still loading
- Confidence on first setup: ~70% (cautious)

### **After 5 Trades** (Data growing)
- Iceberg zones: +2 new zones detected today
- Win rate: 4/5 (80%)
- Edge decay: 0.72 (stronger)
- Session learning: Today's patterns emerging
- Confidence on setups: ~75-80% (normal)

### **After 15 Trades** (Patterns clear)
- Today's best setup identified: Iceberg (80% today)
- Session learning: "London loves icebergs"
- Edge decay: 0.78 (very strong)
- Multiple memories converge on same signal
- Confidence on setups: ~85-95% (aggressive)

### **End of Day** (Full learning)
- New zones recorded for future sessions
- Session performance locked in
- Edge strength validated
- System ready for tomorrow with more data

### **Tomorrow** (System improved)
- Starts with yesterday's memories
- Recognizes recurring zones from yesterday
- Session learning applies (if same session time)
- More confident from day 1
- ✨ System got smarter overnight!

---

## Architecture Summary

```
                    11 MEMORY ENGINES
                           ▼
                    Record every event
                           ▼
                  Query 5 seconds (every bar)
                           ▼
                  Calculate confidence
                           ▼
                     Make decision
                           ▼
                   Display in AI Panel
                           ▼
                   Execute trade (or wait)
                           ▼
                   Record outcome
                           ▼
              ✨ System learns & improves ✨
```

---

## Conclusion

**All 11 memory engines are fully implemented, integrated, and updating in real-time.**

Each engine serves a specific purpose:
- **Trade Memory** = Performance baseline
- **3 Iceberg Memories** = Zone expertise  
- **Signal Memory** = Setup validation
- **Performance Memory** = Risk metrics
- **Cycle Memory** = Timing confirmation
- **Session Learning** = Adaptive strategy
- **Edge Decay** = Position sizing
- **News Memory** = Event risk
- **Structure Memory** = Multi-timeframe alignment

**Together they create an AI that learns from every trade and improves daily.** 🚀
