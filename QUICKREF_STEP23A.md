# STEP 23-A — QUICKREF (ONE-PAGE)

## Files Created (6 modules + 1 test)

```
backtesting/
├── replay_engine.py        # Core loop
├── ai_snapshot.py          # Brain capture + export
├── trade_outcome.py        # Outcome measurement  
├── edge_metrics.py         # Professional metrics
├── replay_runner.py        # Entry point
├── replay_config.py        # Configuration
└── __init__.py             # Exports

test_step23_first.py       # Working example
```

---

## One-Line Usage

```python
from backtesting import run_replay, replay_report
result = run_replay(candles, engines)
report = replay_report(result)
```

---

## Test It Now

```bash
cd /workspaces/quantum-market-observer-
python test_step23_first.py
```

**Expected output**: 1,440 candles, 202 signals, timing accuracy 29.8 bars

---

## What Replay Measures

| What | Why | Target |
|------|-----|--------|
| Timing Accuracy | When do reversals happen? | <20 bars |
| Liquidity Respect | Does price react at zones? | >80% |
| False Signal Rate | High confidence that fail? | <10% |
| Max Heat | Worst adverse move? | <15 pips |
| Clean Hold Rate | Reaction/heat ratio ≥2? | >30% |
| Edge Decay | Does it degrade in chop? | Not detected |

---

## Load Real Data

### CME GC (COMEX Gold)

```python
from data.cme_client import CMEClient

client = CMEClient()
candles = client.get_candles(
    asset="GC",
    timeframe=1,
    start_date="2025-01-06",
    end_date="2025-01-10"
)

result = run_replay(candles, {
    "qmo": your_qmo,
    "imo": your_imo,
    "gann": your_gann,
    "astro": your_astro,
    "cycle": your_cycle,
    "mentor": your_mentor,
})
```

### XAUUSD (Forex Gold)

Use same code, change `asset="XAUUSD"`

---

## Export Results

```python
# Export all snapshots to JSON
result["snapshots"].export_json("snapshots.json")

# Export signals to CSV (quick review)
result["snapshots"].export_signals_csv("signals.csv")

# Print institutional report
print(replay_report(result))
```

---

## Core Loop (How It Works)

```
FOR i, candle in enumerate(candles):
    qmo = engines["qmo"].update(candle)
    imo = engines["imo"].update(candle)
    gann = engines["gann"].update(candle)
    astro = engines["astro"].update(candle)
    cycle = engines["cycle"].update(i)
    
    decision = engines["mentor"].evaluate({
        "price": candle["close"],
        "qmo": qmo,
        "imo": imo,
        "gann": gann,
        "astro": astro,
        "cycle": cycle,
    })
    
    snapshot = {
        "time": candle["time"],
        "price": candle["close"],
        "decision": decision,
        "qmo": qmo,
        ...all engine states...
    }
    
    # Measure outcome
    outcome = analyzer.evaluate_signal(
        snapshot, 
        candles[i+1:i+31]  # next 30 bars
    )
```

---

## Rules (DO NOT BREAK)

✅ **Lock rules before replay**  
✅ **Use real historical data**  
✅ **Measure edge, not profit**  
❌ **No curve fitting**  
❌ **No indicator optimizing**  
❌ **No changing rules mid-test**

---

## When STEP 23-A Is Done

- ✓ Candles processed sequentially ✓ AI decisions recorded
- ✓ Outcomes measured (reaction vs heat)
- ✓ Professional metrics calculated
- ✓ No profit curves, no optimization
- ✓ Ready for 23-B (session + news awareness)

---

## Next: Reply with **23-B**

When ready for:
- Session-aware replay
- News timestamp injection
- Iceberg persistence scoring
- Visual replay hooks

