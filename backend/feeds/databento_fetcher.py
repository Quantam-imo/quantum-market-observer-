"""
Databento Market Data Fetcher - Institutional Grade
Real-time L1/L2/L3 data for iceberg detection and volume profile
CME Gold Futures (GC) - Professional orderflow data
"""

import databento as db
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, AsyncGenerator
import os
from collections import defaultdict


class DatabentoCMLiveStream:
    """
    Databento connection manager for CME Gold Futures
    Handles L1 (price), L2 (volume profile), L3 (iceberg detection)
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DATABENTO_API_KEY")
        if not self.api_key:
            raise ValueError("❌ DATABENTO_API_KEY not found. Set environment variable or pass to constructor.")
        
        self.symbol = "GCG6"  # Gold Futures - Feb 2026 front month contract
        self.dataset = "GLBX.MDP3"  # CME Globex
        self.client = None
        self.is_connected = False
        
        # Cache for latest data
        self.latest_price = None
        self.latest_bid_ask = None
        self.volume_profile = defaultdict(int)  # price -> cumulative volume
        self.iceberg_zones = []
        
        print(f"📊 Databento initialized for {self.symbol} on {self.dataset}")
        print(f"🔑 API Key: {self.api_key[:8]}***")
        
    async def test_connection(self) -> bool:
        """
        Test Databento connection and schema access
        Returns True if connection successful
        """
        try:
            print("\n🔍 Testing Databento connection...")
            print(f"📡 Dataset: {self.dataset}")
            print(f"🎯 Symbol: {self.symbol}")
            
            # Test with Live client (v0.69.0 API)
            self.client = db.Live(
                key=self.api_key
            )
            
            print("✅ Client created successfully")
            print("🚀 Subscribing to market data...")
            
            # Subscribe to trades schema (not async in v0.69.0)
            self.client.subscribe(
                dataset=self.dataset,
                schema="trades",
                symbols=[self.symbol]
            )
            
            self.is_connected = True
            
            print("✅ Subscription successful!")
            print("📥 Waiting for first message...")
            
            # Get first few messages to verify
            count = 0
            for msg in self.client:
                count += 1
                print(f"📨 Message #{count}: Type={type(msg).__name__}")
                
                if hasattr(msg, 'price'):
                    print(f"   💰 Price: {msg.price / 1e9:.2f}")  # Databento uses fixed-point
                
                if count >= 3:
                    print(f"\n✅ SUCCESS! Received {count} messages from Databento")
                    print(f"🎉 Connection test PASSED")
                    break
                    
            return True
            
        except db.BentoError as e:
            print(f"❌ Databento error: {e}")
            print("💡 Check:")
            print("   1. API key is correct")
            print("   2. You have access to GLBX.MDP3 dataset")
            print("   3. Symbol 'GC' is available in your subscription")
            return False
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            if self.client and hasattr(self.client, 'stop'):
                try:
                    self.client.stop()
                except:
                    pass
                self.is_connected = False
                
    async def check_schema_access(self) -> Dict[str, bool]:
        """
        Check which schemas (L1/L2/L3) are available
        Critical for determining iceberg detection capability
        """
        schemas_to_check = {
            "trades": "L1 - Basic price data",
            "tbbo": "L1 - Top of book (bid/ask)",
            "mbp-1": "L2 - Market by price (1 level)",
            "mbp-10": "L2 - Market by price (10 levels) - VOLUME PROFILE",
            "mbo": "L3 - Market by order - ICEBERG DETECTION",
        }
        
        results = {}
        
        for schema, description in schemas_to_check.items():
            try:
                print(f"\n🔍 Testing schema: {schema} ({description})")
                
                test_client = db.Live(
                    key=self.api_key,
                    dataset=self.dataset,
                    schema=schema,
                    symbols=[self.symbol],
                )
                
                test_client.start()
                
                # Try to get one message
                for msg in test_client:
                    print(f"   ✅ {schema}: AVAILABLE")
                    results[schema] = True
                    break
                    
                test_client.stop()
                
            except Exception as e:
                print(f"   ❌ {schema}: NOT AVAILABLE - {str(e)[:50]}")
                results[schema] = False
                
        print("\n" + "="*60)
        print("📊 SCHEMA ACCESS SUMMARY:")
        print("="*60)
        
        for schema, available in results.items():
            status = "✅ YES" if available else "❌ NO"
            print(f"{schema:15} → {status:8} ({schemas_to_check[schema]})")
            
        print("="*60)
        
        # Critical check for iceberg detection
        if results.get("mbo", False):
            print("\n🎯 ICEBERG DETECTION: ✅ AVAILABLE (L3 access confirmed)")
        else:
            print("\n⚠️  ICEBERG DETECTION: ❌ NOT AVAILABLE")
            print("💡 Contact Databento to upgrade to L3 (mbo) schema access")
            
        return results
        
    async def stream_l1_trades(self, callback=None, duration_seconds: int = 10):
        """
        Stream live L1 trade data
        For initial testing and price updates
        """
        try:
            print(f"\n🚀 Starting L1 trade stream for {duration_seconds} seconds...")
            
            self.client = db.Live(
                key=self.api_key,
                dataset=self.dataset,
                schema="trades",
                symbols=[self.symbol],
            )
            
            self.client.start()
            self.is_connected = True
            
            start_time = asyncio.get_event_loop().time()
            trade_count = 0
            
            for msg in self.client:
                trade_count += 1
                
                # Extract trade data
                trade_data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "symbol": self.symbol,
                    "price": getattr(msg, 'price', None),
                    "size": getattr(msg, 'size', None),
                    "side": getattr(msg, 'side', None),
                }
                
                print(f"💹 Trade #{trade_count}: ${trade_data['price']} x {trade_data['size']}")
                
                if callback:
                    await callback(trade_data)
                    
                # Check duration
                if asyncio.get_event_loop().time() - start_time > duration_seconds:
                    print(f"\n✅ Streamed {trade_count} trades in {duration_seconds}s")
                    break
                    
        except Exception as e:
            print(f"❌ Stream error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.client:
                self.client.stop()
                self.is_connected = False
                
    async def stream_l2_depth(self, callback=None, duration_seconds: int = 10):
        """
        Stream L2 market depth for volume profile
        Shows bid/ask volume at each price level
        """
        try:
            print(f"\n🚀 Starting L2 depth stream for {duration_seconds} seconds...")
            
            self.client = db.Live(
                key=self.api_key,
                dataset=self.dataset,
                schema="mbp-10",  # 10 levels of depth
                symbols=[self.symbol],
            )
            
            self.client.start()
            self.is_connected = True
            
            start_time = asyncio.get_event_loop().time()
            update_count = 0
            
            for msg in self.client:
                update_count += 1
                
                # Extract depth data
                depth_data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "symbol": self.symbol,
                    "bid_levels": [],
                    "ask_levels": [],
                }
                
                # Parse bid/ask levels
                for i in range(10):
                    try:
                        bid_price = getattr(msg, f'bid_px_{i:02d}', None)
                        bid_size = getattr(msg, f'bid_sz_{i:02d}', None)
                        ask_price = getattr(msg, f'ask_px_{i:02d}', None)
                        ask_size = getattr(msg, f'ask_sz_{i:02d}', None)
                        
                        if bid_price and bid_size:
                            depth_data["bid_levels"].append({"price": bid_price, "size": bid_size})
                        if ask_price and ask_size:
                            depth_data["ask_levels"].append({"price": ask_price, "size": ask_size})
                    except:
                        pass
                        
                print(f"\n📊 Depth Update #{update_count}:")
                print(f"   BID: {len(depth_data['bid_levels'])} levels")
                print(f"   ASK: {len(depth_data['ask_levels'])} levels")
                
                if callback:
                    await callback(depth_data)
                    
                # Check duration
                if asyncio.get_event_loop().time() - start_time > duration_seconds:
                    print(f"\n✅ Streamed {update_count} depth updates in {duration_seconds}s")
                    break
                    
        except Exception as e:
            print(f"❌ Stream error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.client:
                self.client.stop()
                self.is_connected = False


# ============= TESTING FUNCTIONS =============

async def test_databento_connection():
    """
    Run complete connection test suite
    """
    print("="*70)
    print("🧪 DATABENTO CONNECTION TEST SUITE")
    print("="*70)
    
    # Check for API key
    api_key = os.getenv("DATABENTO_API_KEY")
    if not api_key:
        print("\n❌ ERROR: DATABENTO_API_KEY environment variable not set")
        print("\n💡 To fix:")
        print("   export DATABENTO_API_KEY='your_api_key_here'")
        print("   or set it in your .env file")
        return False
        
    try:
        fetcher = DatabentoCMLiveStream(api_key=api_key)
        
        # Test 1: Basic connection
        print("\n" + "="*70)
        print("TEST 1: Basic Connection")
        print("="*70)
        success = await fetcher.test_connection()
        
        if not success:
            print("\n❌ Basic connection failed. Fix this before proceeding.")
            return False
            
        # Test 2: Schema access
        print("\n" + "="*70)
        print("TEST 2: Schema Access Check")
        print("="*70)
        schemas = await fetcher.check_schema_access()
        
        # Test 3: Live L1 stream
        print("\n" + "="*70)
        print("TEST 3: Live L1 Trade Stream (5 seconds)")
        print("="*70)
        await fetcher.stream_l1_trades(duration_seconds=5)
        
        # Test 4: Live L2 stream (if available)
        if schemas.get("mbp-10", False):
            print("\n" + "="*70)
            print("TEST 4: Live L2 Depth Stream (5 seconds)")
            print("="*70)
            await fetcher.stream_l2_depth(duration_seconds=5)
            
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    """
    Run this file directly to test Databento connection:
    
    python backend/feeds/databento_fetcher.py
    """
    asyncio.run(test_databento_connection())
