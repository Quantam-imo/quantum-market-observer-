# QUICK START: 5-MIN CANDLE PREDICTION

## What You Get

A **5-minute candle prediction panel** that shows:
- 🟢 **BULLISH** (Green) - Next 5-min candle likely UP
- 🔴 **BEARISH** (Red) - Next 5-min candle likely DOWN  
- ⚪ **NEUTRAL** (Gray) - Balanced, expect sideways

**With confidence scores** (0-95%) + **AI insights** + **Memory learning**

---

## How It Works

```
Live Orders from Market
    ↓
Analyzed for CURRENT 5-minute period ONLY
    ↓
Volume, momentum, acceleration calculated
    ↓
AI Mentor Brain weighs the signal
    ↓
Historical patterns checked for accuracy
    ↓
Confidence score generated (0-95%)
    ↓
Panel displays: 🟢 BULLISH 89%
```

---

## The Prediction Basis

### Volume Analysis
- **Order Flow**: Counts BUY vs SELL orders in current 5-min period
- **Balance**: BUY contracts - SELL contracts = directional bias
- **Momentum**: Is volume accelerating or decelerating?
- **Time-Weighted**: Recent orders weighted heavier (more conviction)

### AI Integration
- Uses MentorBrain for intelligent analysis
- Considers volatility regime
- Applies risk management filters
- Boosts confidence if signal is strong

### Memory Learning
- Stores historical 5-minute patterns
- Finds similar past patterns (±15% match)
- Reports what happened before in similar situations
- Learns from outcomes over time

---

## Confidence Interpretation

| Confidence | Meaning | Action |
|-----------|---------|--------|
| 95% | Extreme signal | Strong conviction trade |
| 80-90% | High probability | Good trade setup |
| 70-79% | Decent signal | Reasonable entry |
| 60-69% | Moderate | Use with caution |
| 50-59% | Weak signal | Wait for clarity |
| <50% | Unclear | No trade |

---

## Prediction Panel Display

```
🟢 5-MIN CANDLE: BULLISH ⬆️
Confidence: 89%

📊 ORDER FLOW (5-MIN PERIOD)
⬆️ BUY: 105 contracts (77%)
⬇️ SELL: 31 contracts (23%)
Balance: +74
Total Orders: 12

📈 VOLUME DYNAMICS
Momentum: ACCELERATING
Acceleration: +0.45

🤖 AI MENTOR
Decision: EXECUTE
Regime: TRENDING

🧠 MEMORY PATTERNS
Similar Patterns: 15
Historical Accuracy: 80%

💡 REASONING
Strong buy bias + Volume ACCELERATING
AI confirms signal + Historical patterns 80% success
```

---

## Using For Trading

1. **High Confidence (≥80%)**
   - 🟢 BULLISH 85% → Consider LONG
   - 🔴 BEARISH 82% → Consider SHORT

2. **Medium Confidence (70-79%)**
   - Good signal but not maximum
   - Use with other confirmations
   - Smaller position size

3. **Low Confidence (<50%)**
   - Market is confused/balanced
   - Wait for clarity
   - Don't force trades

---

## Real-Time Updates

- ⏰ Updates **every 5 seconds**
- 📊 Uses **LIVE order data**
- 🔄 **Prediction changes** as orders arrive
- 🎯 **No delays** or lag

---

## Where to Find It

1. **Open Trading Page**: localhost:5500/frontend/index.html
2. **Look Top-Right**: AI Prediction Panel should appear
3. **Monitor Console**: F12 → Console → Watch for "🎯 5-Min Prediction" logs
4. **Hard Refresh** if not showing: Ctrl+Shift+R

---

## Key Features

✅ **5-Minute Specific** - Only analyzes orders from current 5-min period
✅ **Volume-Driven** - Based on real order flow, not price
✅ **AI-Powered** - MentorBrain makes intelligent decisions
✅ **Learning System** - Improves from historical patterns
✅ **Real-Time** - Updates continuously as orders arrive

---

## Example Scenarios

### Scenario 1: Strong Bullish Signal
```
90 BUY orders vs 20 SELL orders
Balance: +70
Momentum: ACCELERATING
AI Decision: EXECUTE
Confidence: 95%

ACTION: Strong BUY signal - consider long entry
```

### Scenario 2: Mixed Orders  
```
55 BUY orders vs 50 SELL orders
Balance: +5
Momentum: STEADY
Confidence: 50%

ACTION: Unclear signal - wait for directional clarity
```

### Scenario 3: Bearish Reversal
```
30 BUY orders vs 75 SELL orders
Balance: -45
Momentum: ACCELERATING
Confidence: 92%

ACTION: Strong SELL signal - consider short entry
```

---

## FAQ

**Q: Does this work on all timeframes?**
A: This is 5-minute specific, but can be adapted for other timeframes.

**Q: How accurate is it?**
A: Depends on order flow quality and market conditions. Memory system tracks accuracy over time.

**Q: Why does prediction change every 5 seconds?**
A: Because new orders arrive! As order flow changes, so does the prediction. This is GOOD - it's responsive.

**Q: Can I trade on confidence <50%?**
A: Not recommended. Wait for a clearer signal (60%+) for better risk/reward.

**Q: What if confidence jumps from 80% to 30%?**
A: Means a large sell order just arrived, reversing the bias. The system is accurate - orders DO reverse predictions!

**Q: Does it work during market gaps?**
A: Works best during active trading. During low volume, signals are weaker (lower confidence).

---

## API Endpoints (For Developers)

**Get Prediction:**
```
POST /api/v1/candle/5min/predict
Response: Full prediction with volumes, momentum, AI insights, patterns
```

**Get Stats:**
```
GET /api/v1/candle/5min/stats
Response: Accuracy metrics, pattern count, success rates
```

---

## Documentation

For detailed technical documentation:
→ Read: `CANDLE_PREDICTION_5MIN_GUIDE.md`

---

**Ready to trade?** Hard refresh your browser and look for the prediction panel! 🎯
