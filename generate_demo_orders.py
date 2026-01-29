#!/usr/bin/env python3
"""
Generate continuous demo orders for testing the 5-minute candle predictor
Creates realistic order flow with randomization
"""
import time
import random
from datetime import datetime
import sys

sys.path.insert(0, '/workspaces/quantum-market-observer-')
from backend.intelligence.order_recorder import RawOrderRecorder

def generate_demo_orders():
    """Generate continuous demo orders"""
    recorder = RawOrderRecorder()
    
    print("🔄 Starting demo order generator...")
    print("📊 Generating orders every 2-5 seconds")
    print("Press Ctrl+C to stop\n")
    
    base_price = 2650.00  # Gold price base
    order_count = 0
    
    try:
        while True:
            # Random order generation
            side = random.choice(['BUY', 'SELL'])
            size = random.choice([5, 8, 10, 12, 15, 20, 25, 30])
            
            # Price variation around base price
            price_offset = random.uniform(-5.0, 5.0)
            price = round(base_price + price_offset, 2)
            
            # Record order
            recorder.record_order(
                timestamp=datetime.utcnow(),
                price=price,
                size=size,
                side=side,
                contract_type='GC'
            )
            
            order_count += 1
            print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Order #{order_count}: {side} {size} @ ${price}")
            
            # Randomize timing (2-5 seconds between orders)
            sleep_time = random.uniform(2.0, 5.0)
            time.sleep(sleep_time)
            
            # Occasionally create bursts of orders (simulate institutional flow)
            if random.random() < 0.15:  # 15% chance
                burst_side = random.choice(['BUY', 'SELL'])
                burst_count = random.randint(3, 7)
                print(f"  💥 BURST: {burst_count} {burst_side} orders")
                
                for _ in range(burst_count):
                    burst_size = random.choice([15, 20, 25, 30, 35])
                    burst_price = round(price + random.uniform(-1.0, 1.0), 2)
                    
                    recorder.record_order(
                        timestamp=datetime.utcnow(),
                        price=burst_price,
                        size=burst_size,
                        side=burst_side,
                        contract_type='GC'
                    )
                    order_count += 1
                    time.sleep(0.5)  # Quick burst
                
    except KeyboardInterrupt:
        print(f"\n\n✅ Stopped. Generated {order_count} total orders")

if __name__ == "__main__":
    generate_demo_orders()
