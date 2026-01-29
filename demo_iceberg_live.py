"""
LIVE ICEBERG DETECTION - CME Gold Futures
Detects institutional orderflow in real-time
"""
import databento as db
from datetime import datetime, timezone
import os
import sys

# Add backend to path
sys.path.insert(0, '/workspaces/quantum-market-observer-/backend')
from feeds.iceberg_detector import IcebergDetector, IcebergZone, IcebergSide

def run_live_iceberg_detection(duration_seconds=60):
    """Run live iceberg detection on Gold Futures"""
    
    api_key = os.getenv("DATABENTO_API_KEY")
    
    print("=" * 80)
    print("❄️  LIVE ICEBERG DETECTION - CME GOLD FUTURES (GC)")
    print("=" * 80)
    print(f"Symbol: GCG6 (February 2026 Contract)")
    print(f"Schema: trades (L1 - Price + Volume)")
    print(f"Duration: {duration_seconds} seconds")
    print(f"API Key: {api_key[:12]}***")
    print("=" * 80)
    print()
    
    # Initialize detector
    detector = IcebergDetector(
        min_executions=5,        # Need 5+ trades at same price
        volume_multiplier=2.5,   # Volume must be 2.5x average
        time_window_seconds=30,  # 30-second detection window
        min_confidence=0.65,     # 65% confidence threshold
    )
    
    try:
        # Create Databento Live client
        client = db.Live(key=api_key)
        
        # Subscribe to Gold Futures trades
        client.subscribe(
            dataset="GLBX.MDP3",
            schema="trades",
            symbols=["GCG6"]
        )
        
        print("✅ Connected to Databento")
        print("📡 Streaming live orderflow...")
        print("🔍 Watching for iceberg patterns...")
        print()
        
        message_count = 0
        iceberg_count = 0
        start_time = datetime.now()
        
        # Process live stream
        for msg in client:
            message_count += 1
            now = datetime.now(timezone.utc)
            
            # Extract trade data
            if hasattr(msg, 'price') and hasattr(msg, 'size'):
                price = msg.price  # Already in correct format
                size = msg.size
                side = getattr(msg, 'side', 'B')  # Default to buy
                
                # Process through iceberg detector
                iceberg = detector.process_trade(
                    price=price,
                    size=size,
                    side='buy' if side == 'B' else 'sell',
                    timestamp=now,
                )
                
                # New iceberg detected!
                if iceberg:
                    iceberg_count += 1
                    print()
                    print("🚨" + "=" * 78 + "🚨")
                    print(f"   ❄️  ICEBERG DETECTED #{iceberg_count}")
                    print("🚨" + "=" * 78 + "🚨")
                    print(f"   💰 Price: ${iceberg.price:.2f}")
                    print(f"   📊 Side: {iceberg.side.value} ABSORPTION")
                    print(f"   📦 Volume: {iceberg.total_volume:,} contracts")
                    print(f"   🔁 Executions: {iceberg.execution_count}")
                    print(f"   ⚡ Avg Size: {iceberg.avg_size_per_execution:.1f}")
                    print(f"   🎯 Confidence: {iceberg.confidence:.1%}")
                    print(f"   📈 Concentration: {iceberg.concentration_ratio:.1f}x normal")
                    print(f"   ⏰ First Seen: {iceberg.first_seen.strftime('%H:%M:%S')}")
                    print("🚨" + "=" * 78 + "🚨")
                    print()
                
                # Status update every 100 messages
                if message_count % 100 == 0:
                    stats = detector.get_stats()
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    print(f"📊 [{elapsed:.0f}s] Messages: {message_count} | "
                          f"Icebergs: {stats['active_icebergs']} active "
                          f"({stats['buy_icebergs']}🟢 / {stats['sell_icebergs']}🔴) | "
                          f"Avg Vol: {stats['avg_execution_size']:.0f}")
                
                # Expire old icebergs
                if message_count % 50 == 0:
                    detector.expire_old_icebergs(now)
            
            # Check duration
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= duration_seconds:
                print(f"\n⏰ Duration complete: {duration_seconds}s")
                break
        
        # Stop client
        client.stop()
        
        # Final statistics
        stats = detector.get_stats()
        print()
        print("=" * 80)
        print("📊 FINAL STATISTICS")
        print("=" * 80)
        print(f"Duration: {elapsed:.1f} seconds")
        print(f"Messages processed: {message_count:,}")
        print(f"Trades analyzed: {stats['total_executions']:,}")
        print(f"Total volume: {stats['total_volume']:,} contracts")
        print(f"Average execution: {stats['avg_execution_size']:.1f} contracts")
        print()
        print(f"🎯 ICEBERGS DETECTED: {iceberg_count}")
        print(f"   Active zones: {stats['active_icebergs']}")
        print(f"   🟢 Buy absorption: {stats['buy_icebergs']}")
        print(f"   🔴 Sell absorption: {stats['sell_icebergs']}")
        print(f"   📚 Historical: {stats['historical_count']}")
        print("=" * 80)
        
        # Show active icebergs
        if detector.get_active_icebergs():
            print()
            print("❄️  ACTIVE ICEBERG ZONES:")
            print("-" * 80)
            for iz in detector.get_active_icebergs():
                print(f"   {iz}")
            print("-" * 80)
        
    except KeyboardInterrupt:
        print("\n⏸️  Stopped by user")
        
    except db.BentoError as e:
        print(f"\n❌ Databento Error: {e}")
        print("💡 Check:")
        print("   - API key is valid")
        print("   - GLBX.MDP3 subscription active")
        print("   - Market hours (CME Gold trades Sunday 5pm - Friday 4pm CT)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                 ICEBERG DETECTION - LIVE DEMO                      ║")
    print("║                                                                    ║")
    print("║  Detecting hidden institutional orders in CME Gold Futures        ║")
    print("║  Using real-time orderflow analysis                               ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Run for 60 seconds
    run_live_iceberg_detection(duration_seconds=60)
