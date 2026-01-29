"""
Live Order Feed - Real/Simulated Market Data
Records trades with Indian Standard Time (IST)
Falls back to simulation if live market is closed
"""

import os
import sys
import time
import random
from datetime import datetime
import pytz
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.intelligence.order_recorder import RawOrderRecorder

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

class LiveOrderFeed:
    """Stream live/simulated trades to order recorder"""
    
    def __init__(self, use_databento=True):
        self.use_databento = use_databento
        self.api_key = os.getenv("DATABENTO_API_KEY")
        self.recorder = RawOrderRecorder()
        self.base_price = 2650.0  # Gold base price
        
        print("=" * 70)
        print("🌐 LIVE ORDER FEED - MARKET DATA")
        print("=" * 70)
        print(f"⏰ Timezone: Indian Standard Time (IST)")
        print(f"💾 Database: {self.recorder.db_path}")
        print("=" * 70)
        
    def run_databento(self):
        """Try to connect to Data Bento live feed"""
        try:
            import databento as db
            
            print("\n🚀 Connecting to Data Bento Live API...")
            client = db.Live(key=self.api_key)
            
            # Try multiple contract months (Z5=Dec 2025, G6=Feb 2026, H6=Mar 2026)
            for symbol in ["GCZ5", "GCG6", "GCH6"]:
                try:
                    print(f"📥 Trying {symbol}...")
                    client.subscribe(
                        dataset="GLBX.MDP3",
                        schema="trades",
                        symbols=[symbol]
                    )
                    print(f"✅ Connected to {symbol}!")
                    return self._process_databento_stream(client, symbol)
                except Exception as e:
                    print(f"⚠️  {symbol} not available: {e}")
                    continue
                    
            print("❌ No live contracts available")
            return False
            
        except Exception as e:
            print(f"❌ Data Bento connection failed: {e}")
            return False
    
    def _process_databento_stream(self, client, symbol):
        """Process Data Bento stream"""
        print("\n" + "=" * 70)
        print(f"LIVE TRADE STREAM - {symbol} (Press Ctrl+C to stop)")
        print("=" * 70)
        
        count = 0
        for msg in client:
            count += 1
            
            if hasattr(msg, 'price') and hasattr(msg, 'size'):
                ts_nano = msg.ts_event if hasattr(msg, 'ts_event') else msg.ts_recv
                ts_ist = datetime.fromtimestamp(ts_nano / 1e9).astimezone(IST)
                
                price = msg.price / 1e9
                size = msg.size if hasattr(msg, 'size') else 1
                side = 'BUY' if hasattr(msg, 'side') and msg.side == 'B' else 'SELL'
                
                self.recorder.record_order(
                    timestamp=ts_ist.isoformat(),
                    price=price,
                    size=size,
                    side=side,
                    contract_type='GC'
                )
                
                if count % 10 == 0:
                    time_str = ts_ist.strftime('%H:%M:%S')
                    balance = self.recorder.get_order_flow_balance(minutes=5)
                    print(f"[{time_str}] Trade #{count:4d}: "
                          f"{'🟢' if side == 'BUY' else '🔴'} {side:4s} "
                          f"{size:3d} @ ${price:,.2f} | Balance: {balance:+d}")
        
        return True
        
    def run_simulated(self):
        """Run simulated market data with realistic patterns"""
        print("\n📊 Running SIMULATED market data (Indian timezone)")
        print("💡 Realistic order flow patterns for testing")
        print("\n" + "=" * 70)
        print("SIMULATED TRADE STREAM (Press Ctrl+C to stop)")
        print("=" * 70)
        
        count = 0
        price = self.base_price
        
        try:
            while True:
                count += 1
                
                # Get IST timestamp
                ts_ist = datetime.now(IST)
                
                # Random walk price with mean reversion
                price_change = random.uniform(-2, 2) + (self.base_price - price) * 0.1
                price += price_change
                
                # Realistic size distribution (mostly small, occasional large)
                if random.random() < 0.9:
                    size = random.randint(1, 20)  # 90% small orders
                else:
                    size = random.randint(50, 200)  # 10% institutional
                
                # Side with slight buy bias during uptrends
                if price > self.base_price:
                    side = 'BUY' if random.random() < 0.55 else 'SELL'
                else:
                    side = 'SELL' if random.random() < 0.55 else 'BUY'
                
                # Record order
                self.recorder.record_order(
                    timestamp=ts_ist.isoformat(),
                    price=price,
                    size=size,
                    side=side,
                    contract_type='GC'
                )
                
                # Print every 10 trades
                if count % 10 == 0:
                    time_str = ts_ist.strftime('%H:%M:%S')
                    balance = self.recorder.get_order_flow_balance(minutes=5)
                    print(f"[{time_str}] Trade #{count:4d}: "
                          f"{'🟢' if side == 'BUY' else '🔴'} {side:4s} "
                          f"{size:3d} @ ${price:,.2f} | Balance: {balance:+d}")
                
                # Random delay (1-5 seconds between trades)
                time.sleep(random.uniform(1, 5))
                
        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("🛑 Feed stopped by user")
            print(f"✅ Recorded {count} simulated trades")
            print("=" * 70)
    
    def run(self):
        """Start feed (try Data Bento, fall back to simulation)"""
        if self.use_databento:
            success = self.run_databento()
            if success:
                return
        
        # Fall back to simulation
        print("\n💡 Using simulated data (market closed or no live access)")
        time.sleep(2)
        self.run_simulated()


if __name__ == "__main__":
    feed = LiveOrderFeed(use_databento=True)
    feed.run()

