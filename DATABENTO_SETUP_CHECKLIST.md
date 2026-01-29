# Databento Integration Checklist

## Overview
This checklist guides you through setting up Databento for the QMO system.

---

## Phase 1: Account & Setup

### [ ] 1.1 Create Databento Account
- [ ] Go to https://databento.com
- [ ] Sign up for free trial
- [ ] Complete email verification
- [ ] Create workspace/organization

### [ ] 1.2 Subscribe to GLBX.MDP3 Dataset
- [ ] In Databento dashboard, navigate to "Datasets"
- [ ] Search for "GLBX.MDP3" (CME Globex)
- [ ] Click "Subscribe" or "Request Access"
- [ ] Wait for approval (usually instant)

### [ ] 1.3 Check Schema Access
- [ ] In Databento dashboard, go to "Schemas"
- [ ] Verify you have access to:
  - [ ] `trades` (L1 - Price)
  - [ ] `tbbo` (L1 - Bid/Ask)
  - [ ] `mbp-1` (L2 - Basic depth)
  - [ ] `mbp-10` (L2 - **IMPORTANT** Volume Profile)
  - [ ] `mbo` (L3 - *Optional* Iceberg Detection) [Premium]

### [ ] 1.4 Get API Key
- [ ] In Databento dashboard, go to "API Keys"
- [ ] Click "Create New API Key"
- [ ] Name it "QMO-Production"
- [ ] Copy the key (looks like: `abc123def456...`)
- [ ] Store securely (will only show once)

---

## Phase 2: Local Environment Setup

### [ ] 2.1 Install Databento SDK
```bash
pip install databento
```
- [ ] Verify: `python -c "import databento; print(databento.__version__)"`

### [ ] 2.2 Set Environment Variable
**Option A: Shell (temporary)**
```bash
export DATABENTO_API_KEY="your_api_key_here"
echo $DATABENTO_API_KEY  # Verify it shows up
```

**Option B: Permanent (.bashrc or .zshrc)**
```bash
echo 'export DATABENTO_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**Option C: .env file**
```bash
# Create .env in project root
echo 'DATABENTO_API_KEY=your_api_key_here' > .env

# In Python, load with:
from dotenv import load_dotenv
load_dotenv()
```

- [ ] Verify: `echo $DATABENTO_API_KEY` shows your key

### [ ] 2.3 Verify System Has Databento Code
```bash
# Check files exist
ls -la backend/feeds/databento_fetcher.py
ls -la backend/feeds/market_data_fetcher.py
ls -la test_databento.py
```
- [ ] All three files exist
- [ ] No errors reading them

---

## Phase 3: Testing Connection

### [ ] 3.1 Run Connection Test
```bash
cd /workspaces/quantum-market-observer-
python test_databento.py
```

**Expected output:**
```
✅ Client created successfully
✅ Connection established!
📨 Message #1: ...
📨 Message #2: ...
📨 Message #3: ...
✅ SUCCESS! Received 3 messages from Databento
```

- [ ] No errors
- [ ] Received at least 3 messages
- [ ] Timestamps are current

### [ ] 3.2 Check Schema Access
```bash
python -c "
import asyncio
from backend.feeds.databento_fetcher import DatabentoCMLiveStream

async def check():
    stream = DatabentoCMLiveStream()
    await stream.test_connection()
    print('✅ Connection OK')
    
asyncio.run(check())
"
```

- [ ] Connection established without errors
- [ ] Can query schema access

### [ ] 3.3 Monitor Live Data
```bash
python -c "
import asyncio
from backend.feeds.databento_fetcher import DatabentoCMLiveStream

async def stream():
    stream = DatabentoCMLiveStream()
    
    async def callback(trade):
        print(f'💹 {trade[\"price\"]} x {trade[\"size\"]}')
    
    await stream.stream_l1_trades(callback, duration_seconds=5)

asyncio.run(stream())
"
```

- [ ] See live price updates
- [ ] Prices match current GC (Gold Futures) market
- [ ] No connection timeouts

---

## Phase 4: Integration into QMO System

### [ ] 4.1 Enable in API Startup
**File: `backend/main.py`**

Find:
```python
@app.on_event("startup")
async def startup_event():
```

Add:
```python
# Initialize live Databento feed
from backend.feeds.market_data_fetcher import MarketDataFetcher
market_fetcher = MarketDataFetcher()

# Start background live feed task
asyncio.create_task(live_market_feed_loop())

async def live_market_feed_loop():
    while True:
        try:
            data = await market_fetcher.fetch_current_price()
            # Route to intelligence engines
            await route_to_engines(data)
        except Exception as e:
            print(f"❌ Feed error: {e}")
        await asyncio.sleep(1)
```

- [ ] Added startup code
- [ ] No syntax errors
- [ ] Imports are correct

### [ ] 4.2 Update Market State Endpoint
**File: `backend/api/routes.py`**

Replace mock data:
```python
# OLD: Uses hardcoded values
market_state = {
    "current_price": 2500.0,
    "bid": 2499.5,
    "ask": 2500.5,
}

# NEW: Use live Databento
@router.post("/api/v1/market")
async def get_market_data():
    live_data = await market_fetcher.fetch_current_price()
    return {
        "price": live_data.price,
        "bid": live_data.bid,
        "ask": live_data.ask,
        "timestamp": live_data.timestamp
    }
```

- [ ] Updated endpoint to use live data
- [ ] Removed hardcoded values
- [ ] Tested with curl/Postman

### [ ] 4.3 Connect to Intelligence Engines
**File: `backend/feeds/stream_router.py`**

```python
async def route_to_engines(market_data):
    """Route live Databento data to all intelligence engines"""
    
    # Iceberg detection (needs L3 mbo data)
    iceberg = await iceberg_detector.process(market_data)
    
    # Absorption zones (needs volume profile)
    absorption = await absorption_engine.process(market_data)
    
    # Orderflow analysis (needs tick data)
    orderflow = await orderflow_engine.process(market_data)
    
    # Store for API response
    global latest_analysis
    latest_analysis = {
        "timestamp": market_data.timestamp,
        "price": market_data.price,
        "iceberg_zones": iceberg,
        "absorption_zones": absorption,
        "orderflow": orderflow
    }
```

- [ ] Stream router created/updated
- [ ] All engines receiving data
- [ ] No import errors

---

## Phase 5: Verification

### [ ] 5.1 Start API Server
```bash
python backend/main.py
```

- [ ] Server starts without errors
- [ ] Port 8000 is listening
- [ ] No Databento connection errors in logs

### [ ] 5.2 Test Market Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/market \
  -H "Content-Type: application/json" \
  -d '{"symbol": "GC"}'
```

Expected response:
```json
{
  "price": 2567.5,
  "bid": 2567.3,
  "ask": 2567.7,
  "timestamp": "2026-01-27T10:30:45Z",
  "iceberg_zones": [...],
  "absorption_zones": [...]
}
```

- [ ] Response includes live price
- [ ] Price updates in real-time
- [ ] No stale cached values
- [ ] All fields present

### [ ] 5.3 Monitor Live Feed
```bash
# Watch logs while running
tail -f /tmp/qmo.log

# Should see:
# 📊 Databento: $2567.5 x 100
# ✅ Absorption detected at 2567.3
# 📈 Confidence: 0.82
```

- [ ] Live price updates showing
- [ ] Intelligence engines processing data
- [ ] No errors in logs

### [ ] 5.4 Test Fallback (Optional)
```bash
# Simulate Databento outage
unset DATABENTO_API_KEY

# Restart server
python backend/main.py

# Should fall back to Yahoo Finance
# Response will have ~15s delay but still work
```

- [ ] Server continues running
- [ ] Falls back to Yahoo Finance gracefully
- [ ] No crash or hang

---

## Phase 6: Performance Tuning

### [ ] 6.1 Add Caching Strategy
```python
# Cache market data for 1 second
CACHE_TTL = 1  # seconds

last_price = None
last_fetch_time = None

async def get_market_data_cached():
    global last_price, last_fetch_time
    
    now = time.time()
    if last_price and (now - last_fetch_time) < CACHE_TTL:
        return last_price  # Return cached
    
    last_price = await market_fetcher.fetch_current_price()
    last_fetch_time = now
    return last_price
```

- [ ] Caching layer added
- [ ] TTL appropriate for market (1-5 seconds)
- [ ] Tested for cache hits

### [ ] 6.2 Add Circuit Breaker
```python
# Fallback if Databento fails N times
FAILURE_THRESHOLD = 5
failure_count = 0

async def get_market_data_safe():
    global failure_count
    
    try:
        data = await market_fetcher.fetch_current_price()
        failure_count = 0  # Reset on success
        return data
    except Exception as e:
        failure_count += 1
        if failure_count >= FAILURE_THRESHOLD:
            print("⚠️  Switching to Yahoo Finance")
            return await yahoo_fetcher.fetch_current_price()
        raise
```

- [ ] Circuit breaker added
- [ ] Automatic fallback implemented
- [ ] Tested with simulated failures

### [ ] 6.3 Add Monitoring/Alerts
```python
# Track feed health
feed_stats = {
    "messages_received": 0,
    "errors": 0,
    "last_update": None,
    "uptime": 0
}

async def monitor_feed():
    while True:
        if time.time() - feed_stats["last_update"] > 5:
            print(f"⚠️  No update for 5 seconds")
            # Send alert
        await asyncio.sleep(1)
```

- [ ] Monitoring enabled
- [ ] Alerting configured
- [ ] Dashboard shows feed health

---

## Phase 7: Production Ready

### [ ] 7.1 Security Checklist
- [ ] API key not hardcoded (using env var)
- [ ] API key not in git commits
- [ ] Add to `.gitignore`: `.env`
- [ ] Rotate API key monthly
- [ ] Use separate key for dev/prod

### [ ] 7.2 Documentation
- [ ] Document setup in README
- [ ] Create operational runbook
- [ ] Document fallback procedures
- [ ] List support contacts for Databento

### [ ] 7.3 Monitoring Setup
- [ ] Add health check endpoint
- [ ] Monitor feed latency
- [ ] Alert on failures
- [ ] Track usage/quota

### [ ] 7.4 Load Testing
```bash
# Simulate 100 requests/second
ab -n 10000 -c 100 http://localhost:8000/api/v1/market
```

- [ ] Handles high load
- [ ] Latency < 200ms
- [ ] No connection drops

---

## Common Issues & Solutions

### ❌ "DATABENTO_API_KEY not found"
**Solution:**
```bash
export DATABENTO_API_KEY="your_key"
python test_databento.py
```

### ❌ "Connection timeout"
**Solution:**
1. Check internet connection
2. Verify API key is correct
3. Check Databento status page
4. Restart application

### ❌ "mbo schema not available"
**Solution:** 
1. Contact Databento support
2. Upgrade plan
3. Use L2 (mbp-10) instead - still good for iceberg detection

### ❌ "Data is stale"
**Solution:**
1. Increase cache TTL
2. Check network latency
3. Verify Databento is streaming
4. Monitor for disconnects

---

## Success Criteria

✅ **All checks completed = System is Production Ready**

- [ ] Databento account created
- [ ] API key configured
- [ ] Connection test passes
- [ ] Live feed integrated
- [ ] Market endpoint returns live data
- [ ] Intelligence engines receiving data
- [ ] Fallback working
- [ ] Monitoring in place
- [ ] Load testing passed
- [ ] Documentation complete

---

## Quick Command Reference

```bash
# Test Databento
python test_databento.py

# Check API key
echo $DATABENTO_API_KEY

# Start QMO with live feed
python backend/main.py

# Check market endpoint
curl http://localhost:8000/api/v1/market

# Watch live data
tail -f /tmp/qmo.log | grep "Databento"

# Test fallback
unset DATABENTO_API_KEY && python backend/main.py
```

---

## When Complete

🎉 **Databento is now feeding live orderflow data to QMO!**

Next steps:
1. Monitor in production
2. Tune thresholds based on live data
3. Expand to other instruments (ES, NQ, etc.)
4. Connect to live broker API for execution

---

**Status**: Ready for implementation  
**Difficulty**: Medium (just API key + configuration)  
**Time Required**: 30-60 minutes
