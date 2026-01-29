"""Find available Gold Futures symbols in Databento"""
import databento as db
import os
from datetime import date

api_key = os.getenv("DATABENTO_API_KEY", "db-DVHPTr5TecV9qr3cwdJGWb5A7iJ38")

print("=" * 70)
print("🔍 SEARCHING FOR GOLD FUTURES SYMBOLS")
print("=" * 70)

try:
    client = db.Historical(key=api_key)
    
    # Search for Gold futures
    print("\n📊 Searching GLBX.MDP3 for Gold (GC) symbols...")
    print("-" * 70)
    
    # Get instrument definitions for Gold
    instruments = client.symbology.resolve(
        dataset="GLBX.MDP3",
        symbols=["GC*"],  # Wildcard search for all GC contracts
        stype_in="raw_symbol",
        stype_out="instrument_id",
        start_date=date(2026, 1, 1)
    )
    
    print(f"\n✅ Found {len(instruments)} Gold Futures symbols:")
    print("-" * 70)
    
    for result in instruments[:10]:  # Show first 10
        print(f"  • Symbol: {result.get('s', result)}")
    
    print("\n" + "=" * 70)
    print("💡 Use the continuous contract symbol for live trading")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
