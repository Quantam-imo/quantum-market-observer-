"""Check if Gold (GC) data is available in Databento GLBX.MDP3"""
import databento as db
import os
from datetime import datetime, timedelta

api_key = os.getenv("DATABENTO_API_KEY")

print("=" * 80)
print("🔍 CHECKING GOLD FUTURES (GC) DATA AVAILABILITY")
print("=" * 80)

client = db.Historical(key=api_key)

# Test multiple time periods
test_dates = [
    datetime.now() - timedelta(days=1),  # Yesterday
    datetime.now() - timedelta(days=7),  # Last week
    datetime.now() - timedelta(days=30), # Last month
]

# Test different symbol formats for Gold
symbol_formats = [
    "GC",           # Simple
    "GCG4",         # Feb 2024 contract
    "GCH4",         # Mar 2024 contract
    "GCJ4",         # Apr 2024 contract
    "GCM4",         # Jun 2024 contract
    "GCZ4",         # Dec 2024 contract
    "GCG5",         # Feb 2025
    "GCH5",         # Mar 2025
    "GCZ5",         # Dec 2025
    "GCG6",         # Feb 2026
    "GCH6",         # Mar 2026
]

print("\n📊 Testing Gold Futures symbols...")
print("-" * 80)

success_found = False

for symbol in symbol_formats:
    for test_date in test_dates:
        try:
            start = test_date.strftime("%Y-%m-%d")
            end = (test_date + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Try to get data
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=[symbol],
                schema="trades",
                start=start,
                end=end,
                limit=5
            )
            
            # Check if we got data
            if data is not None and len(data) > 0:
                df = data.to_df()
                if len(df) > 0:
                    print(f"\n✅ FOUND DATA!")
                    print(f"   Symbol: {symbol}")
                    print(f"   Date: {start}")
                    print(f"   Records: {len(df)}")
                    
                    if 'price' in df.columns:
                        avg_price = df['price'].mean() / 1e9
                        print(f"   Average Price: ${avg_price:.2f}")
                    
                    print(f"\n📋 Sample data:")
                    print(df.head(3))
                    
                    success_found = True
                    
                    # Found working symbol, save it
                    print(f"\n🎉 WORKING SYMBOL: {symbol}")
                    print(f"💡 Use this symbol format for Gold Futures")
                    break
            
        except db.BentoError as e:
            # Symbol not found or no data, continue
            pass
        except Exception as e:
            pass
    
    if success_found:
        break

if not success_found:
    print("\n⚠️  No Gold Futures data found with tested symbols")
    print("\n💡 Possible reasons:")
    print("   1. Gold Futures might use a different symbol format in GLBX.MDP3")
    print("   2. GC might not be included in your subscription")
    print("   3. Need to check CME product codes")
    print("\n📝 Try checking:")
    print("   - ES (S&P 500 E-mini) - Most liquid CME contract")
    print("   - NQ (Nasdaq 100 E-mini)")
    print("   - CL (Crude Oil)")
    
    # Try ES as backup
    print("\n" + "=" * 80)
    print("🔍 Testing ES (S&P 500 E-mini) as backup...")
    print("-" * 80)
    
    try:
        yesterday = datetime.now() - timedelta(days=1)
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols=["ESH6"],  # March 2026 S&P contract
            schema="trades",
            start=yesterday.strftime("%Y-%m-%d"),
            limit=5
        )
        
        if data and len(data) > 0:
            df = data.to_df()
            print(f"✅ ES data available! ({len(df)} records)")
            print(f"💡 System can use ES (S&P 500) if GC not available")
            print(df.head(3))
        
    except Exception as e:
        print(f"⚠️  ES also unavailable: {e}")

print("\n" + "=" * 80)
