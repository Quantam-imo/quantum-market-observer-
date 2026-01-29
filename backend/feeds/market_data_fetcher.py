"""
Market Data Fetcher - Real-time data from Yahoo Finance
Provides live OHLC candlesticks and current market prices
No API key required, no rate limits!
"""

import yfinance as yf
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import random
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MarketDataFetcher:
    """Fetcher for live market data from Yahoo Finance"""
    
    def __init__(self):
        self.symbol = "GC=F"  # Gold Futures (COMEX) - Real live data!
        self.interval = "5m"  # 5-minute candles
        self.cache = {}
        self.last_fetch = {}
        print(f"📊 Yahoo Finance initialized for {self.symbol} (Gold Futures)")
        
    async def fetch_current_price(self) -> Optional[Dict]:
        """Fetch current price for symbol from Yahoo Finance"""
        try:
            # Check price cache - avoid redundant API calls within 15 seconds
            price_cache_key = f"{self.symbol}:price"
            price_ttl = 15
            now = datetime.utcnow()

            if price_cache_key in self.cache and price_cache_key in self.last_fetch:
                age = (now - self.last_fetch[price_cache_key]).total_seconds()
                if age < price_ttl:
                    cached = self.cache[price_cache_key]
                    print(f"✅ Price cache hit (age: {age:.0f}s) - ${cached['current_price']}")
                    return cached

            # Run in thread pool since yfinance is sync
            ticker = await asyncio.to_thread(yf.Ticker, self.symbol)
            info = await asyncio.to_thread(lambda: ticker.info)
            
            if info and 'regularMarketPrice' in info:
                price = info['regularMarketPrice']
                print(f"📊 Yahoo Finance price: ${price}")
                result = {
                    "symbol": self.symbol,
                    "current_price": float(price),
                    "bid": float(info.get('bid', price)),
                    "ask": float(info.get('ask', price)),
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "Yahoo Finance"
                }

                # Cache the price
                self.cache[price_cache_key] = result
                self.last_fetch[price_cache_key] = now
                print(f"💾 Cached current price: ${price}")

                return result
            else:
                print(f"⚠️ No price data in Yahoo Finance response")
        except Exception as e:
            print(f"❌ Error fetching current price from Yahoo Finance: {e}")
            
        return None
    
    async def fetch_ohlc_candles(self, limit: int = 100, interval: str = "5m") -> Optional[List[Dict]]:
        """Fetch OHLC candlesticks from Yahoo Finance for the requested interval."""
        try:
            # Check cache first - avoid redundant API calls within 30-60 seconds
            cache_key = f"{self.symbol}:{interval}"
            cache_ttl = 30 if interval in ["1m", "5m"] else 60
            now = datetime.utcnow()

            if cache_key in self.cache and cache_key in self.last_fetch:
                age = (now - self.last_fetch[cache_key]).total_seconds()
                if age < cache_ttl:
                    cached = self.cache[cache_key]
                    print(f"✅ Cache hit for {interval} (age: {age:.0f}s) - returning {len(cached)} candles")
                    return cached

            yf_interval, period = self._map_interval(interval)
            print(f"📊 Fetching {limit} candles ({interval} -> {yf_interval}, period={period}) for {self.symbol} from Yahoo Finance")
            
            # Fetch historical data - yfinance uses sync calls
            ticker = await asyncio.to_thread(yf.Ticker, self.symbol)
            hist = await asyncio.to_thread(
                lambda: ticker.history(period=period, interval=yf_interval)
            )
            
            if hist is not None and not hist.empty:
                print(f"📊 Yahoo Finance returned {len(hist)} candles")
                candles = []
                
                # Convert DataFrame to our format
                for timestamp, row in hist.iterrows():
                    try:
                        candles.append({
                            "timestamp": timestamp.isoformat(),
                            "open": float(row['Open']),
                            "high": float(row['High']),
                            "low": float(row['Low']),
                            "close": float(row['Close']),
                            "volume": int(row.get('Volume', 0))
                        })
                    except (KeyError, ValueError) as e:
                        print(f"⚠️ Candle parsing error: {e}")
                        continue
                
                # Downsample if user requested a higher timeframe than Yahoo supports (e.g., 4h)
                if interval.lower() == "4h" and yf_interval != "4h":
                    candles = self._resample_multi_hour(candles, 4)
                elif interval.lower() == "1h" and yf_interval in ("60m", "1h"):
                    # Ensure label consistency
                    interval = "1h"
                
                # Return most recent candles up to limit
                candles = candles[-limit:] if len(candles) > limit else candles
                print(f"✅ Parsed {len(candles)} candles successfully")

                # Update cache
                self.cache[cache_key] = candles
                self.last_fetch[cache_key] = now
                print(f"💾 Cached {len(candles)} candles for {interval}")

                return candles if candles else None
            else:
                print(f"⚠️ No historical data returned from Yahoo Finance")
        except Exception as e:
            print(f"❌ Error fetching OHLC from Yahoo Finance: {e}")
            import traceback
            traceback.print_exc()
            
        return None

    def _map_interval(self, interval: str) -> (str, str):
        """Map UI interval to Yahoo Finance interval and period window."""
        interval = (interval or "5m").lower()
        mapping = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "60m",
            "60m": "60m",
            "4h": "60m",  # Fetch 1h and downsample
            "1d": "1d"
        }
        yf_interval = mapping.get(interval, "5m")
        period = "7d" if yf_interval == "1m" else ("60d" if yf_interval in ["60m", "1h"] else "30d")
        return yf_interval, period

    def _resample_multi_hour(self, candles: List[Dict], hours: int) -> List[Dict]:
        """Resample 1h candles into multi-hour aggregates (e.g., 4h)."""
        if not candles:
            return candles
        bucket = []
        resampled = []
        current_bucket = None
        for c in candles:
            dt = datetime.fromisoformat(c["timestamp"])
            bucket_start = dt.replace(minute=0, second=0, microsecond=0)
            bucket_start -= timedelta(hours=dt.hour % hours)
            if current_bucket is None:
                current_bucket = bucket_start
            if bucket_start != current_bucket:
                agg = self._aggregate_bucket(bucket)
                if agg:
                    resampled.append(agg)
                bucket = []
                current_bucket = bucket_start
            bucket.append({**c, "_dt": dt})
        if bucket:
            agg = self._aggregate_bucket(bucket)
            if agg:
                resampled.append(agg)
        return resampled

    def _aggregate_bucket(self, bucket: List[Dict]) -> Optional[Dict]:
        if not bucket:
            return None
        bucket_sorted = sorted(bucket, key=lambda x: x["_dt"])
        open_p = bucket_sorted[0]["open"]
        close_p = bucket_sorted[-1]["close"]
        high_p = max(c["high"] for c in bucket_sorted)
        low_p = min(c["low"] for c in bucket_sorted)
        vol = sum(c.get("volume", 0) for c in bucket_sorted)
        ts = bucket_sorted[-1]["_dt"].isoformat()
        return {
            "timestamp": ts,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": vol
        }
    
    async def fetch_live_market_data(self) -> Dict:
        """Fetch complete live market data from Yahoo Finance"""
        try:
            # Fetch from Yahoo Finance
            price_task = asyncio.create_task(self.fetch_current_price())
            candles_task = asyncio.create_task(self.fetch_ohlc_candles())
            
            price_data = await price_task
            candles_data = await candles_task
            
            # Use Yahoo Finance data or fallback to demo
            if price_data and candles_data:
                print("✅ Yahoo Finance data loaded successfully")
                return {
                    "current_price": price_data["current_price"],
                    "bid": price_data["bid"],
                    "ask": price_data["ask"],
                    "candles": candles_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "live": True,
                    "source": "Yahoo Finance"
                }
            else:
                # Fallback: Generate realistic demo data
                print("⚠️  Using realistic demo data (Yahoo Finance unavailable)")
                return self._generate_realistic_demo_data()
        except Exception as e:
            print(f"❌ Error in fetch_live_market_data: {e}")
            return self._generate_realistic_demo_data()
        except Exception as e:
            print(f"❌ Error in fetch_live_market_data: {e}")
            return self._generate_realistic_demo_data()
    
    def _generate_realistic_demo_data(self) -> Dict:
        """Generate realistic market simulation data"""
        import random
        from datetime import datetime, timedelta
        
        # Base price for gold (realistic)
        base_price = 2450.0
        
        # Generate 100 candles with realistic OHLCV
        candles = []
        current_price = base_price
        
        now = datetime.utcnow()
        for i in range(100, 0, -1):
            # Random walk with trend
            direction = random.choice([-1, -1, -1, 0, 1, 1, 1])  # Bearish bias
            movement = direction * random.uniform(0.5, 2.5)
            current_price += movement
            
            # Generate OHLC
            open_p = current_price
            close_p = current_price + random.uniform(-1.5, 1.5)
            high_p = max(open_p, close_p) + random.uniform(0.5, 2.0)
            low_p = min(open_p, close_p) - random.uniform(0.5, 2.0)
            
            # Volume with spike probability
            base_volume = 5000
            if random.random() < 0.2:
                volume = int(base_volume * random.uniform(2, 4))  # 20% spike chance
            else:
                volume = int(base_volume * random.uniform(0.8, 1.5))
            
            candles.append({
                "timestamp": (now - timedelta(minutes=i*5)).isoformat(),
                "open": round(open_p, 1),
                "high": round(high_p, 1),
                "low": round(low_p, 1),
                "close": round(close_p, 1),
                "volume": volume
            })
        
        return {
            "current_price": round(current_price, 1),
            "bid": round(current_price - 0.2, 1),
            "ask": round(current_price + 0.2, 1),
            "candles": candles,
            "timestamp": datetime.utcnow().isoformat(),
            "live": False,
            "source": "Demo (API Limited)"
        }


# Global fetcher instance
_fetcher = None


async def get_fetcher() -> MarketDataFetcher:
    """Get or create fetcher instance"""
    global _fetcher
    if _fetcher is None:
        _fetcher = MarketDataFetcher()
    return _fetcher


async def fetch_live_market_data() -> Dict:
    """Fetch live market data"""
    fetcher = await get_fetcher()
    return await fetcher.fetch_live_market_data()


async def fetch_current_price() -> Optional[float]:
    """Fetch current price only"""
    fetcher = await get_fetcher()
    data = await fetcher.fetch_current_price()
    return data["current_price"] if data else None


async def fetch_ohlc_candles(limit: int = 100, interval: str = "5m") -> List[Dict]:
    """Fetch OHLC candles for a specific interval."""
    fetcher = await get_fetcher()
    data = await fetcher.fetch_ohlc_candles(limit, interval)
    return data or []


if __name__ == "__main__":
    # Test the fetcher
    async def test():
        data = await fetch_live_market_data()
        print(f"Current Price: {data.get('current_price')}")
        print(f"Candles: {len(data.get('candles', []))} loaded")
        if data.get('candles'):
            print(f"Latest: {data['candles'][0]}")
    
    asyncio.run(test())
