# Real-Time Data Provider & Brokerage Analysis for Iceberg/OrderFlow Trading

## TOP DATA PROVIDERS (Ranked by Suitability)

### 1. **POLYGON.IO** ⭐⭐⭐⭐⭐ (BEST OVERALL)
**Best for: Real-time futures, order flow, volume analysis**

| Feature | Rating | Details |
|---------|--------|---------|
| **Real-Time Latency** | <50ms | Sub-50ms for futures tick data |
| **Iceberg Detection** | ✅ | Tick-by-tick order data available |
| **Volume/OrderFlow** | ✅✅ | Level 2 data with bid/ask volume |
| **Gold Futures** | ✅ | Full access to COMEX GC futures |
| **Historical Data** | ✅✅ | 5+ years of candle/tick data |
| **API** | WebSocket + REST | Extremely fast, reliable |
| **Cost** | $29-249/mo | Enterprise: negotiate |
| **Free Tier** | 100 req/min | Good for development |

**Polygon.IO Setup:**
```
API Base: https://data.polygon.io/v1
WebSocket: wss://socket.polygon.io
Symbols: F.GC (Gold Futures)
Authentication: API key in header
```

---

### 2. **IQFEED (by DTN)** ⭐⭐⭐⭐⭐
**Best for: Serious traders, institutional-grade data**

| Feature | Rating | Details |
|---------|--------|---------|
| **Real-Time Latency** | <100ms | Professional grade |
| **Iceberg Detection** | ✅✅ | Implied order detection built-in |
| **Volume/OrderFlow** | ✅✅ | Time & Sales tape, DOM (Depth of Market) |
| **Gold Futures** | ✅ | All COMEX contracts |
| **Historical Data** | ✅✅ | Unlimited tick data |
| **API** | TCP/WebSocket | Blazing fast |
| **Cost** | $50-200/mo | Enterprise: $500+/mo |
| **Free Tier** | ❌ | Not available |

**IQFEED Pros:**
- **DOM (Depth of Market)** = Direct access to order book
- **Time & Sales** = Every tick with imbalance detection
- **Implied Orders** = Iceberg algo detection built-in
- Used by: ThinkorSwim, e*TRADE, Professional traders

---

### 3. **INTERACTIVE BROKERS (IBAPI)** ⭐⭐⭐⭐
**Best for: Trading + Data (integrated)**

| Feature | Rating | Details |
|---------|--------|---------|
| **Real-Time Latency** | <100ms | Pro-level |
| **Iceberg Detection** | ✅✅ | Order book data + level 2 |
| **Volume/OrderFlow** | ✅✅ | Full DOM access |
| **Gold Futures** | ✅ | GC (COMEX), MGC (Micro) |
| **Cost** | $0 (with trading) | $0 if trading activity |
| **Data Fee** | $10-25/mo | Market data subscription |
| **API** | Python (IB-insync) | Excellent integration |

**Interactive Brokers Advantages:**
- **Trade directly from your app** = No separate broker needed
- **Free data with $125+ monthly trading** 
- **Automatic iceberg handling** = Can place iceberg orders via API
- **Lowest commissions** for futures

---

### 4. **ALPACA** ⭐⭐⭐
**Best for: Stock options (not ideal for futures)**

| Feature | Rating | Details |
|---------|--------|---------|
| **Real-Time Latency** | <100ms | Good for stocks |
| **Iceberg Detection** | ❌ | Stock market only |
| **Futures Support** | ❌ | No crypto, no futures |
| **Cost** | Free | No data costs |
| **Limitation** | Stocks only | Cannot use for gold futures |

---

### 5. **BINANCE/CRYPTO EXCHANGES** (If pivoting to crypto)
**Best for: 24/7 trading, high leverage**

| Exchange | Latency | Features | Cost |
|----------|---------|----------|------|
| **Binance Futures** | <50ms | 1000x leverage, order book | Fee-based |
| **Bybit** | <50ms | Spot + Perpetuals | Competitive |
| **OKX** | <50ms | Full DOM, all order types | Maker rebates |

**Note:** Crypto lacks traditional iceberg orders; instead has "hidden orders"

---

## BEST BROKERAGE FOR YOUR SETUP

### **RECOMMENDED: INTERACTIVE BROKERS** ⭐⭐⭐⭐⭐
**Why:**
1. **All-in-one**: Trade + Real-time data + Order management
2. **Lowest commissions**: $0.85/contract (GC futures)
3. **Free data**: Included if you trade >$125/month
4. **Python API**: Seamless integration with your backend
5. **Iceberg orders**: Native support via API
6. **Order book data**: DOM access for volume analysis
7. **Reliability**: 99.99% uptime for institutional traders

### Setup Cost:
- Account opening: $0
- Minimum deposit: $2,000-$5,000
- Data feeds: $0 (with trading)
- **First year cost: <$1,000** (if trading)

---

### ALTERNATIVE: **POLYGON.IO + NINJATRADER BROKER**
**Best for: Data-first approach**

| Component | Solution | Cost |
|-----------|----------|------|
| **Data** | Polygon.IO | $99/mo (pro tier) |
| **Brokerage** | NinjaTrader Brokerage | $0 comm (Rithmic) |
| **Charting** | Your own (chart.v4.js) | $0 |
| **Order Flow** | Polygon.IO L2 data | Included |

---

## IMPLEMENTATION ROADMAP

### Phase 1: QUICK START (Current - Yahoo Finance)
```python
✅ Data: Yahoo Finance (delayed ~15-20 min)
✅ Cost: $0
⚠️ Limitation: Not real-time
```

### Phase 2: DEVELOPMENT (Polygon.IO + Alpaca)
```python
📊 Data: Polygon.IO (real-time futures)
💰 Brokerage: Alpaca (practice account, no commissions)
💻 Setup: 2-3 hours
💵 Cost: $29-99/mo
✅ Good for: Building, backtesting
```

### Phase 3: LIVE TRADING (Interactive Brokers)
```python
🚀 Data: Interactive Brokers API
💱 Trading: Live commissions
🎯 Order Flow: Full DOM access
📈 Cost: $0-500/mo (based on volume)
✅ Best for: Real money, professional use
```

---

## DATA INTEGRATION PRIORITY

For **iceberg + orderflow + volume**:

1. **MUST HAVE:**
   - Tick-by-tick order data (not just OHLC)
   - Bid/Ask volume at each price level
   - Time & Sales tape (every trade)
   - Order imbalance detection

2. **NICE TO HAVE:**
   - Depth of Market (DOM) - top 20 levels
   - Implied orders (algo detection)
   - Session volumes (open interest)
   - Trading halts/news feed

3. **POLYGON.IO provides all of this:**
   ```
   GET /v3/quotes/{ticker}           → Real-time bid/ask
   GET /v3/trades/{ticker}            → Every tick
   GET /v3/aggs/ticker/{ticker}/range → OHLCV candles
   WebSocket /stocks/trades           → Live tick stream
   ```

---

## CODE EXAMPLE: Polygon.IO Integration

```python
# backend/feeds/polygon_fetcher.py

import asyncio
import aiohttp
from polygon import RESTClient
from polygon.websocket.stocks import StocksClient
from polygon.websocket.option_details import OptionDetails

class PolygonFetcher:
    def __init__(self, api_key: str):
        self.client = RESTClient(api_key)
        self.ws = StocksClient(api_key)
        self.symbol = "F:GC"  # Gold Futures
        
    async def fetch_real_time_ticks(self):
        """Stream real-time tick data with orderflow"""
        
        def handle_trade(trade):
            print(f"🔴 TRADE: ${trade.price} x {trade.size} @ {trade.timestamp}")
            
        def handle_quote(quote):
            bid_vol = quote.bid_size
            ask_vol = quote.ask_size
            imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)
            print(f"💹 BID: ${quote.bid} ({bid_vol}) | ASK: ${quote.ask} ({ask_vol}) | Imbalance: {imbalance:.2%}")
            
        self.ws.on_trade("F:GC", handle_trade)
        self.ws.on_quote("F:GC", handle_quote)
        await self.ws.connect()
        
    async def fetch_dom(self):
        """Get Depth of Market (top 20 levels)"""
        # Note: Requires Polygon Pro tier
        snapshot = self.client.get_last_quote("F:GC")
        return {
            "bid": snapshot.bid,
            "bid_size": snapshot.bid_size,
            "ask": snapshot.ask,
            "ask_size": snapshot.ask_size,
            "imbalance": (snapshot.bid_size - snapshot.ask_size) / (snapshot.bid_size + snapshot.ask_size)
        }
```

---

## COST COMPARISON

| Provider | Startup | Monthly | Year 1 | Notes |
|----------|---------|---------|--------|-------|
| **Yahoo Finance** | $0 | $0 | $0 | Delayed 15-20 min |
| **Polygon.IO** | $0 | $29-99 | $350-1,200 | Real-time, best value |
| **IQFEED** | $0 | $50+ | $600+ | Professional grade |
| **Interactive Brokers** | $0 | $0-500 | $0-6,000 | Best if trading live |
| **Alpaca + Polygon** | $0 | $99-129 | $1,188-1,548 | Good hybrid |

---

## FINAL RECOMMENDATION

**For your project (iceberg + orderflow + volume):**

### 🏆 BEST: **Polygon.IO + Interactive Brokers**

**Why:**
1. **Polygon.IO** for data ($99/mo professional tier)
   - Real-time tick data (<50ms)
   - Level 2 orderflow (bid/ask volume)
   - Iceberg detection from order patterns
   
2. **Interactive Brokers** for trading ($0 if you trade)
   - Place iceberg orders via API
   - Get filled at best prices
   - Pay commissions only on trades

3. **Timeline**: 3-4 weeks to full integration
4. **Cost**: $99/mo data + trading commissions only
5. **Uptime**: 99.99% professional reliability

**Start with:**
```bash
# 1. Sign up: polygon.io (get free tier API key)
# 2. Sign up: interactivebrokers.com (open paper trading account)
# 3. Replace market_data_fetcher.py with polygon_fetcher.py
# 4. Update API calls in FastAPI routes
# 5. Test with paper trading first
```

---

## ACTION ITEMS

- [ ] Sign up for Polygon.IO free tier: https://polygon.io
- [ ] Apply for Interactive Brokers: https://www.interactivebrokers.com
- [ ] Request IB API documentation
- [ ] Implement Polygon WebSocket in backend
- [ ] Test iceberg order detection with real tick data
- [ ] Backtest on 3 months of historical data
- [ ] Go live with paper trading
- [ ] Transition to live account with real capital
