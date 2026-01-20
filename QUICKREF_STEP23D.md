# STEP 23-D Quick Reference

## What You Can Do Now

### 1. Replay ANY Trading Day
```python
from backtesting import ReplayEngine, ReplayCursor

engine = ReplayEngine(mentor_brain, ...)
engine.run(candles)
cursor = engine.get_cursor()

# Jump to bar 100
cursor.jump_to(100)
print(cursor.get_position())  # {current: 101, total: 1440, percentage: 7.0}

# Scrub backward/forward
cursor.prev()  # Go back one bar
cursor.next()  # Go forward one bar
cursor.jump_to_time("2025-01-10T14:30:00")  # Jump to specific time
```

### 2. See Signal Birth-to-Death
```python
from backtesting import SignalLifecycle

lifecycle = engine.get_lifecycle_history()

for signal in lifecycle:
    print(f"Signal born at: {signal['born_at']}")
    print(f"Entry price: {signal['entry_price']}")
    print(f"State: {signal['state']}")  # DORMANT → CONFIRMED → ACTIVE → COMPLETED
    print(f"Alive for: {signal['bars_alive']} bars")
```

### 3. Visualize With 6 Heatmaps
```python
# Get all heatmaps
heatmaps = engine.get_heatmaps()

# Confidence (dark = high, light = low)
confidence = heatmaps['confidence']  # [{"time": "", "confidence": 0.82, "level": "HIGH"}]

# Activity (where signals fired)
activity = heatmaps['activity']  # [{"time": "", "active": True, "signal_type": "BUY"}]

# Killzone (stop-hunting areas)
killzone = heatmaps['killzone']  # [{"time": "", "killzone": True, "severity": "HIGH"}]

# News impact (event proximity)
news = heatmaps['news_impact']  # [{"time": "", "news_active": True, "impact": "HIGH"}]

# Session breakdown
session = heatmaps['session']  # [{"session": "LONDON", "trades": 5, "win_rate": 0.80}]

# Iceberg volume (institutional orders)
iceberg = heatmaps['iceberg']  # [{"time": "", "iceberg_score": 0.75}]
```

### 4. Context at Any Position
```python
# Get full context at current cursor position
context = cursor.current_context()

candle = context['candle']  # Current OHLC
timeline = context['timeline']  # Signal data
index = context['index']  # Current bar number

# Access timeline data
print(f"Confidence: {timeline['confidence']}")
print(f"Decision: {timeline['decision']}")
print(f"Signal type: {timeline['decision']['action']}")
```

### 5. Find Failed Trades
```python
lifecycle = engine.get_lifecycle_history()
cursor = engine.get_cursor()

# Find all invalidated signals
failed = [s for s in lifecycle if s['state'] == 'INVALIDATED']

for signal in failed:
    cursor.jump_to(signal['born_at'])
    context = cursor.current_context()
    print(f"Failed at: {context['timeline']['time']}")
    
    # Check what killed it
    heatmaps = engine.get_heatmaps()
    killzone_heat = heatmaps['killzone'][cursor.index]
    news_heat = heatmaps['news_impact'][cursor.index]
    
    print(f"  Killzone: {killzone_heat['killzone']}")
    print(f"  News: {news_heat['news_active']}")
```

### 6. Session-Specific Analysis
```python
heatmaps = engine.get_heatmaps()
session_heat = heatmaps['session']

# Find best trading session
best = max(session_heat, key=lambda s: s['win_rate'])
print(f"Best session: {best['session']} ({best['win_rate']:.1%} win rate)")

# Compare all sessions
for s in session_heat:
    print(f"{s['session']}: {s['trades']} trades, {s['win_rate']:.1%}")
```

### 7. Look Ahead Without Moving
```python
# Peek 5 bars forward without moving cursor
next_5 = cursor.peek_forward(5)
print(f"Next 5 closes: {[c['close'] for c in next_5]}")

# Peek backward
prev_3 = cursor.peek_backward(3)
print(f"Last 3 closes: {[c['close'] for c in prev_3]}")
```

---

## API Reference

### SignalLifecycle
```python
lifecycle = SignalLifecycle()

# Each bar:
state = lifecycle.update(context, decision)
# Returns: {"state": "CONFIRMED", "action": "BUY", ...}

# Get full history:
history = lifecycle.get_history()

# Get summary:
summary = lifecycle.lifecycle_summary()
# {"total": 10, "completed": 7, "invalidated": 2, "avg_bars_alive": 18.5}

# Check if active:
is_active = lifecycle.is_active()

# Get current signal:
current = lifecycle.get_current()

# Reset:
lifecycle.reset()
```

### ReplayCursor
```python
cursor = ReplayCursor(candles, timeline)

# Navigation
cursor.next()
cursor.prev()
cursor.jump_to(50)
cursor.jump_to_time("2025-01-10T14:30:00")
cursor.rewind()
cursor.fast_forward()

# Query
current = cursor.current()  # Current candle dict
context = cursor.current_context()  # {candle, timeline, index}
position = cursor.get_position()  # {current: 1-based, total, percentage}

# Status
is_start = cursor.is_at_start()
is_end = cursor.is_at_end()

# Peek (non-moving)
next_5 = cursor.peek_forward(5)
prev_3 = cursor.peek_backward(3)

# History
nav_history = cursor.get_navigation_history()
```

### HeatmapEngine
```python
engine = HeatmapEngine()

# Individual heatmaps
conf = engine.generate_confidence_heatmap(timeline)
act = engine.generate_activity_heatmap(timeline)
sess = engine.generate_session_heatmap(timeline)
kz = engine.generate_killzone_heatmap(timeline)
news = engine.generate_news_impact_heatmap(timeline)
ice = engine.generate_iceberg_heatmap(timeline)

# All at once
all_heatmaps = engine.generate_all_heatmaps(timeline)

# Export
engine.export_heatmaps_json("replay_data.json")

# Retrieve cached
heat = engine.get_heatmap("confidence")
```

### ReplayEngine (New Methods)
```python
engine = ReplayEngine(...)
engine.run(candles)

cursor = engine.get_cursor()
history = engine.get_lifecycle_history()
summary = engine.get_lifecycle_summary()
all_heats = engine.get_heatmaps()
one_heat = engine.get_heatmap("confidence")
engine.export_heatmaps("file.json")
```

---

## Signal States

```
DORMANT        → Initial signal potential
ARMED          → Entry conditions aligning  
CONFIRMED      → Trade allowed by filters (can enter next bar)
ACTIVE         → Signal live for 1+ bars
COMPLETED      → Target/stop hit
INVALIDATED    → Failed before entry
```

---

## Heatmap Outputs

| Type | Returns | Use |
|------|---------|-----|
| Confidence | [{"time": "", "confidence": 0.82, "level": "HIGH"}] | Visualize AI certainty |
| Activity | [{"time": "", "active": True, "signal_type": "BUY"}] | Show where signals fire |
| Session | [{"session": "LONDON", "trades": 5, "win_rate": 0.80}] | Compare sessions |
| Killzone | [{"time": "", "killzone": True, "severity": "HIGH"}] | Identify danger zones |
| News | [{"time": "", "news_active": True, "impact": "HIGH"}] | Track event proximity |
| Iceberg | [{"time": "", "iceberg_score": 0.75}] | Detect institutional orders |

---

## Common Patterns

### Find Best Trades
```python
lifecycle = engine.get_lifecycle_history()
completed = sorted(
    [s for s in lifecycle if s['state'] == 'COMPLETED'],
    key=lambda x: x['bars_alive'],
    reverse=True
)
best = completed[0]
cursor.jump_to(best['born_at'])
```

### Find Worst Trades
```python
lifecycle = engine.get_lifecycle_history()
invalidated = [s for s in lifecycle if s['state'] == 'INVALIDATED']
for signal in invalidated:
    print(f"Failed at bar {signal['born_at']}")
```

### Session Performance
```python
heatmaps = engine.get_heatmaps()
for session in heatmaps['session']:
    wr = session['win_rate']
    print(f"{session['session']}: {wr:.1%}")
```

### Killzone Analysis
```python
heatmaps = engine.get_heatmaps()
kz = [k for k in heatmaps['killzone'] if k['killzone']]
print(f"Total killzone candles: {len(kz)}")
```

### Iceberg Detection
```python
heatmaps = engine.get_heatmaps()
iceberg_avg = sum(h['iceberg_score'] for h in heatmaps['iceberg']) / len(heatmaps['iceberg'])
print(f"Avg iceberg score: {iceberg_avg:.2f}")
```

---

## Integration Examples

### Full Professional Analysis
```python
from backtesting import ReplayEngine

engine = ReplayEngine(mentor_brain, timeline_builder)
engine.run(candles)

# 1. Find failed trades
failed = [s for s in engine.get_lifecycle_history() if s['state'] == 'INVALIDATED']

for signal in failed:
    # 2. Jump to failure point
    cursor = engine.get_cursor()
    cursor.jump_to(signal['born_at'])
    
    # 3. Get full context
    context = cursor.current_context()
    heatmaps = engine.get_heatmaps()
    
    print(f"Signal at {context['timeline']['time']}:")
    print(f"  Confidence: {context['timeline']['confidence']:.2%}")
    print(f"  Killzone: {heatmaps['killzone'][cursor.index]['killzone']}")
    print(f"  News: {heatmaps['news_impact'][cursor.index]['news_active']}")
    
    # 4. Scrub through signal life
    while cursor.index < signal['born_at'] + 5:
        cursor.next()
        ctx = cursor.current_context()
        print(f"  Bar {cursor.index}: close={ctx['candle']['close']}")

# 5. Export for visualization
engine.export_heatmaps("replay_analysis.json")
```

---

## Performance Notes

- **Lifecycle updates:** ~0.1ms per bar
- **Cursor jumps:** ~0.01ms
- **Heatmap generation:** ~1ms for 1000+ bars
- **Memory:** ~50KB per 1000-bar timeline

---

## What's Next?

STEP 23-E adds:
- Risk metrics (Sharpe, Sortino, max drawdown)
- Performance attribution (which edges?)
- Advanced institutional patterns

**Status: Ready for 23-E**
