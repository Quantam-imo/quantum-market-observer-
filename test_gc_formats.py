"""Test different Gold Futures symbol formats"""
import databento as db
import os

api_key = os.getenv("DATABENTO_API_KEY")

# Try different symbol formats
symbols_to_try = [
    "GC.FUT",     # Continuous futures format
    "GC.c.0",     # Continuous contract 0
    "GCH26",      # March 2026 contract
    "GCJ26",      # April 2026 contract  
    "GCM26",      # June 2026 contract
    "GC",         # Simple format
]

print("=" * 70)
print("🧪 TESTING GOLD FUTURES SYMBOL FORMATS")
print("=" * 70)

for symbol in symbols_to_try:
    print(f"\n🔍 Trying symbol: {symbol}")
    try:
        client = db.Live(key=api_key)
        client.subscribe(
            dataset="GLBX.MDP3",
            schema="trades",
            symbols=[symbol]
        )
        
        # Try to get first message
        count = 0
        for msg in client:
            if hasattr(msg, '__class__'):
                msg_type = type(msg).__name__
                print(f"  ✅ SUCCESS! Got {msg_type}")
                
                if hasattr(msg, 'price'):
                    price = msg.price / 1e9
                    print(f"  💰 Price: ${price:.2f}")
                
                client.stop()
                print(f"\n🎉 WORKING SYMBOL: {symbol}")
                break
            
            count += 1
            if count > 5:
                print(f"  ⏱️ Timeout waiting for data")
                client.stop()
                break
                
    except db.BentoError as e:
        print(f"  ❌ Failed: {e}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
print("\n" + "=" * 70)
