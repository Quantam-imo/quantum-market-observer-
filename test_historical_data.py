"""Check Databento connectivity with historical data"""
import databento as db
import os
from datetime import datetime, timedelta

api_key = os.getenv("DATABENTO_API_KEY")

print("=" * 70)
print("🔍 DATABENTO HISTORICAL DATA TEST")
print("=" * 70)

try:
    client = db.Historical(key=api_key)
    
    # Get data from yesterday
    yesterday = datetime.now() - timedelta(days=1)
    start_date = yesterday.strftime("%Y-%m-%d")
    
    print(f"\n📊 Fetching Gold Futures data from {start_date}...")
    print("   Dataset: GLBX.MDP3")
    print("   Schema: trades")
    print("   Symbols: ES.FUT (S&P 500 - more active)")
    print("-" * 70)
    
    # Try ES instead of GC (more liquid, easier to get data)
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["ES.FUT"],  # S&P 500 futures (most liquid)
        schema="trades",
        start=start_date,
        limit=10
    )
    
    print(f"\n✅ Successfully retrieved data!")
    print(f"📦 Data type: {type(data)}")
    print(f"📊 Data shape: {data.shape if hasattr(data, 'shape') else 'N/A'}")
    
    if hasattr(data, 'to_df'):
        df = data.to_df()
        print(f"\n📈 First few records:")
        print(df.head())
        
        if 'price' in df.columns:
            print(f"\n💰 Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
    
    print("\n" + "=" * 70)
    print("✅ DATABENTO CONNECTION VERIFIED!")
    print("💡 Your API key works - live streaming requires market hours")
    print("=" * 70)
    
except db.BentoError as e:
    print(f"❌ Databento Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
