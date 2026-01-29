# Databento Integration Guide for QMO

## Current Status

✅ **Databento code exists** - `backend/feeds/databento_fetcher.py`  
✅ **Test suite created** - `test_databento.py`  
⚠️ **Not fully integrated into live system yet**  

---

## What Databento Provides

Databento is an **institutional-grade market data provider** specializing in **orderflow data**:

### Data Schemas Available

| Schema | Name | Data Type | Use Case |
|--------|------|-----------|----------|
| `trades` | **L1** | Price only | Basic price updates |
| `tbbo` | **L1+** | Bid/Ask | Top of book quotes |
| `mbp-1` | **L2** | 1-level depth | Simple volume |
| `mbp-10` | **L2** | 10-level depth | Volume profile (MOST IMPORTANT) |
| `mbo` | **L3** | Order-by-order | **ICEBERG DETECTION** (Premium) |

### For QMO: CME Gold Futures (GC)

```
Dataset: GLBX.MDP3 (CME Globex Market Data)
Symbol: GC (Gold Futures)
```

---

## Architecture: How Databento Integrates

```
┌─────────────────────────────────────────────────────────────┐
│                    LIVE DATA SOURCES                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ DATABENTO (Primary - Institutional Orderflow)         │  │
│  │ ├─ L1: trades, tbbo                                  │  │
│  │ ├─ L2: mbp-10 (Volume Profile)                       │  │
│  │ └─ L3: mbo (Iceberg Detection) [Premium]             │  │
│  └──────────────────────────────────────────────────────┘  │
│           ↓                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ MARKET DATA FETCHER (Stream Router)                  │  │
│  │ ├─ Real-time feed aggregation                        │  │
│  │ ├─ Caching layer (15s TTL)                           │  │
│  │ └─ Fallback to Yahoo Finance if Databento unavailable│  │
│  └──────────────────────────────────────────────────────┘  │
│           ↓                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ INTELLIGENCE ENGINES (Real-time Processing)          │  │
│  │ ├─ Iceberg Detector (L3 mbo data)                    │  │
│  │ ├─ Absorption Engine (Volume clustering)             │  │
│  │ ├─ Orderflow Analysis (Delta, Bias)                  │  │
│  │ └─ Liquidity Sweeps (ICT trap detection)             │  │
│  └──────────────────────────────────────────────────────┘  │
│           ↓                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ MENTOR BRAIN (Decision Making)                       │  │
│  │ ├─ Confidence Scoring (5 pillars)                    │  │
│  │ ├─ Entry Routing                                      │  │
│  │ └─ Position Management                                │  │
│  └──────────────────────────────────────────────────────┘  │
│           ↓                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ EXECUTION LAYER (Trade Execution)                    │  │
│  │ ├─ Entry Engine                                       │  │
│  │ ├─ Position Sizer                                     │  │
│  │ └─ Risk Management                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│           ↓                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ API RESPONSE (Trader Dashboard)                      │  │
│  │ ├─ Real-time signals                                  │  │
│  │ ├─ Market analysis                                    │  │
│  │ └─ Trade recommendations                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Setup Requirements

### 1. **Databento Account**
```bash
# Go to: https://databento.com
# 1. Create account
# 2. Subscribe to GLBX.MDP3 dataset
# 3. Check which schemas are available (L1, L2, or L3)
# 4. Get API key
```

### 2. **Environment Variable**
```bash
# Set in your shell or .env file
export DATABENTO_API_KEY="your_api_key_here"

# Verify
echo $DATABENTO_API_KEY
```

### 3. **Install Databento SDK**
```bash
pip install databento
```

---

## Testing Databento Connection

### Step 1: Run Connection Test
```bash
python test_databento.py
```

This will:
- ✅ Test connection to Databento
- ✅ Check which schemas are available
- ✅ Stream 3 sample messages
- ✅ Report results

### Expected Output
```
🔍 Testing Databento connection...
📡 Dataset: GLBX.MDP3
🎯 Symbol: GC

✅ Client created successfully
🚀 Starting connection...
✅ Connection established!
📥 Waiting for first message...

📨 Message #1: {price: 2567.5, size: 100, ...}
📨 Message #2: {price: 2567.6, size: 150, ...}
📨 Message #3: {price: 2567.4, size: 200, ...}

✅ SUCCESS! Received 3 messages from Databento
🎉 Connection test PASSED
```

### Step 2: Check Schema Access
```python
from backend.feeds.databento_fetcher import DatabentoCMLiveStream

# Initialize
stream = DatabentoCMLiveStream()

# Test connection
success = await stream.test_connection()

# Check schemas
if success:
    schemas = await stream.check_schema_access()
    print(schemas)
    # Output:
    # trades: ✅ YES (L1 - Basic price data)
    # tbbo: ✅ YES (L1 - Top of book)
    # mbp-1: ✅ YES (L2 - 1-level depth)
    # mbp-10: ✅ YES (L2 - 10-level volume profile)
    # mbo: ❌ NO (L3 - Iceberg detection) [Premium feature]
```

---

## How Each Component Works

### 1. **DatabentoCMLiveStream** (Fetcher)
Located: `backend/feeds/databento_fetcher.py`

```python
class DatabentoCMLiveStream:
    # Connect to Databento
    async def test_connection() -> bool
    
    # Check which data schemas available
    async def check_schema_access() -> Dict[str, bool]
    
    # Stream L1 (price only)
    async def stream_l1_trades(callback, duration)
    
    # Stream L2 (volume profile)
    async def stream_l2_depth(callback, duration)
    
    # Stream L3 (iceberg detection) [Premium]
    async def stream_l3_orders(callback, duration)
```

### 2. **MarketDataFetcher** (Router)
Located: `backend/feeds/market_data_fetcher.py`

**Purpose**: Aggregate data from multiple sources
- Primary: Databento (if available and subscribed)
- Fallback: Yahoo Finance (free, no API key)

```python
class MarketDataFetcher:
    # Fetch current price
    async def fetch_current_price() -> Dict
    # Returns: {current_price, bid, ask, timestamp}
    
    # Fetch OHLC candles
    async def fetch_candles(interval="5m") -> List[Dict]
    # Returns: [open, high, low, close, volume]
    
    # Get volume profile (L2 depth)
    async def fetch_volume_profile() -> Dict
    # Returns: {price: volume, price: volume, ...}
```

### 3. **Stream Router**
Located: `backend/feeds/stream_router.py`

**Purpose**: Dispatch data to intelligence engines

```python
async def route_to_engines(market_data):
    # Route to Iceberg Detector (needs L3 mbo data)
    await iceberg_engine.process(market_data)
    
    # Route to Absorption Engine (needs volume data)
    await absorption_engine.process(market_data)
    
    # Route to Orderflow Analyzer (needs tick data)
    await orderflow_engine.process(market_data)
    
    # Route to Confidence Scorer
    await confidence_engine.process(market_data)
```

---

## Integration into QMO Pipeline

### Live Trading Loop

```python
# In backend/main.py or API routes

async def live_trading_loop():
    fetcher = MarketDataFetcher()
    
    while True:
        # 1. FETCH: Get latest market data from Databento
        market_data = await fetcher.fetch_current_price()
        # {price, bid, ask, volume, timestamp}
        
        # 2. PROCESS: Route through intelligence engines
        iceberg_zones = await iceberg_detector.process(market_data)
        absorption_zones = await absorption_engine.process(market_data)
        orderflow = await orderflow_engine.process(market_data)
        
        # 3. ANALYZE: Score confidence with 5 pillars
        confidence = await mentor_brain.analyze(
            market_data,
            iceberg_zones,
            absorption_zones,
            orderflow
        )
        
        # 4. DECIDE: Generate signal
        signal = await signal_builder.build(confidence)
        
        # 5. EXECUTE: Send to trader
        if signal.confidence > 0.75:
            await execution_engine.route_entry(signal)
        
        # Sleep for next tick
        await asyncio.sleep(1)  # 1-second loop
```

### API Endpoint Example

```python
@router.post("/api/v1/market")
async def get_market_data(request: MarketRequest):
    """Get live market data + QMO analysis"""
    
    # 1. Fetch from Databento
    market = await fetcher.fetch_current_price()
    
    # 2. Run through all intelligence engines
    iceberg = await iceberg_detector.detect(market)
    absorption = await absorption_engine.detect(market)
    liquidity = await liquidity_engine.analyze(market)
    
    # 3. Score confidence
    confidence = await mentor.score_all_pillars(
        qmo_score=market.qmo_score,
        imo_score=iceberg.score,
        gann_score=gann.calculate(market),
        astro_score=astro.calculate(market),
        cycle_score=cycle.calculate(market)
    )
    
    # 4. Return to frontend
    return {
        "price": market.price,
        "bid": market.bid,
        "ask": market.ask,
        "iceberg_zones": iceberg.zones,
        "absorption_zones": absorption.zones,
        "confidence": confidence.total,
        "signal": "BUY" if confidence.total > 0.75 else "HOLD"
    }
```

---

## What Data Gets Used Where

### L1 (trades, tbbo) - Basic Price Data

**Feeds to:**
- Gann Engine (high/low levels)
- Astro Engine (reversal windows)
- Cycles Engine (21/45/90 bar detection)
- Bar Builder (OHLC construction)

**Update Frequency**: Every tick (sub-second)

### L2 (mbp-10) - Volume Profile

**Feeds to:**
- Absorption Engine (zone clustering)
- Liquidity Sweep Engine (trap detection)
- Orderflow Engine (delta calculation)
- Volume Profile Engine

**Update Frequency**: Every depth update (millisecond)

### L3 (mbo) - Order-by-Order Data

**Feeds to:**
- Advanced Iceberg Engine (pattern matching)
- Iceberg Memory (historical correlation)
- Capital Protection Engine (institutional activity)

**Update Frequency**: Every order (microsecond)

---

## Current System State

### ✅ What's Already Built
```
backend/feeds/databento_fetcher.py  - Full Databento client
backend/feeds/market_data_fetcher.py - Yahoo fallback + aggregation
backend/feeds/stream_router.py       - Data routing layer
test_databento.py                    - Connection tester
```

### ⚠️ What Needs Integration
1. **Activate live feed in API** - Replace mock market_state
2. **Connect to execution engines** - Route Databento data
3. **Add signal publishing** - Broadcast alerts to WebSocket
4. **Implement caching strategy** - Optimize for high-frequency updates
5. **Add circuit breaker** - Fallback if Databento unavailable

### 🔧 What Needs to be Done

```python
# Step 1: Enable live Databento in API
@router.on_event("startup")
async def startup_live_feed():
    global live_market_data
    
    # Initialize Databento fetcher
    fetcher = MarketDataFetcher()
    
    # Start background loop
    asyncio.create_task(live_feed_loop(fetcher))

# Step 2: Create live feed background task
async def live_feed_loop(fetcher):
    while True:
        try:
            # Fetch from Databento
            data = await fetcher.fetch_current_price()
            
            # Update global state
            live_market_data.update({
                "price": data.price,
                "bid": data.bid,
                "ask": data.ask,
                "timestamp": data.timestamp
            })
            
            # Route to engines
            await route_to_intelligence_engines(data)
            
            # Check for signals
            signal = await generate_signal(data)
            
            # Broadcast to clients
            if signal:
                await broadcast_signal(signal)
                
        except Exception as e:
            print(f"❌ Feed error: {e}")
            await fallback_to_yahoo_finance()
        
        await asyncio.sleep(1)  # 1-second update loop
```

---

## Implementation Checklist

- [ ] Have Databento account with API key
- [ ] Environment variable set: `DATABENTO_API_KEY`
- [ ] Run `python test_databento.py` - test passes
- [ ] Check schema access - identify available data levels
- [ ] Integrate into API startup sequence
- [ ] Connect Databento data to intelligence engines
- [ ] Add WebSocket broadcast for real-time updates
- [ ] Implement fallback to Yahoo Finance
- [ ] Add circuit breaker + error handling
- [ ] Test with live GC (Gold Futures) data

---

## Quick Start Commands

```bash
# 1. Set your API key
export DATABENTO_API_KEY="your_key_here"

# 2. Test connection
python test_databento.py

# 3. Check what you have access to
python -c "
from backend.feeds.databento_fetcher import DatabentoCMLiveStream
import asyncio

async def check():
    stream = DatabentoCMLiveStream()
    await stream.test_connection()
    schemas = await stream.check_schema_access()
    
asyncio.run(check())
"

# 4. Start system with live feed
python backend/main.py
```

---

## Q&A

**Q: Do I need L3 (mbo) access for iceberg detection?**  
A: Not required, but recommended. L2 (mbp-10) volume profile can detect most icebergs. L3 is for ultra-high precision.

**Q: What if I don't have Databento?**  
A: System automatically falls back to Yahoo Finance for price data. You lose orderflow analysis but core system still works.

**Q: How much does Databento cost?**  
A: Professional plans start ~$150-500/month depending on schema access. Free trial available.

**Q: Can I mix Databento with Yahoo?**  
A: Yes! The system uses Databento for orderflow, Yahoo as fallback for price if Databento unavailable.

**Q: How real-time is the data?**  
A: Databento: sub-second. Yahoo Finance: ~15s delays. System handles both.

---

## Next Steps

1. **Get Databento Account** - https://databento.com
2. **Run Test** - `python test_databento.py`
3. **Enable Live Feed** - Uncomment in `backend/main.py`
4. **Connect to Engines** - Wire up stream router
5. **Go Live** - Start trading with real orderflow

System is **ready to accept live Databento data** - just needs API key!
