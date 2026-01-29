"""
Volume Profile Indicator Test & Usage Guide
=============================================

The Volume Profile indicator shows the distribution of trading volume across price levels.
This is a critical tool for identifying:
- POC (Point of Control): Price with highest volume
- VAH/VAL (Value Area High/Low): Boundaries containing 70% of volume
- VWAP (Volume Weighted Average Price): Institutional benchmark

API Endpoint: POST /api/v1/indicators/volume-profile

Request Parameters:
- symbol: Trading symbol (e.g., "GCG6" for Gold Futures)
- interval: Chart interval (e.g., "5m", "15m", "1h")
- bars: Number of bars to analyze (default: 100)
- tick_size: Price granularity (0.10 for gold futures)
- value_area_pct: Percentage for value area calculation (default: 0.70 = 70%)

Response Data:
- poc: Point of Control (highest volume price)
- vah: Value Area High
- val: Value Area Low
- vwap: Volume Weighted Average Price
- total_volume: Total volume across all price levels
- histogram: Array of price levels with volume distribution
  - price: Price level
  - volume: Volume at this price
  - volume_pct: Percentage of total volume (POC = 100%)
  - is_poc: True if this is the Point of Control
  - in_value_area: True if price is in 70% value area
"""

import requests
import json

# Test the Volume Profile endpoint
def test_volume_profile():
    url = "http://localhost:8000/api/v1/indicators/volume-profile"
    
    payload = {
        "symbol": "GCG6",
        "interval": "5m",
        "bars": 50,
        "tick_size": 0.10,
        "value_area_pct": 0.70
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        
        print("=" * 60)
        print("VOLUME PROFILE ANALYSIS")
        print("=" * 60)
        print(f"Symbol: {data['symbol']}")
        print(f"Interval: {data['interval']}")
        print(f"Bars Analyzed: {data['bars_analyzed']}")
        print(f"Total Volume: {data['total_volume']:,}")
        print()
        print("KEY LEVELS:")
        print(f"  POC (Point of Control): ${data['poc']:.2f}")
        print(f"  VAH (Value Area High):  ${data['vah']:.2f}")
        print(f"  VAL (Value Area Low):   ${data['val']:.2f}")
        print(f"  VWAP:                   ${data['vwap']:.2f}")
        print()
        
        # Show value area range
        value_area_range = data['vah'] - data['val']
        print(f"Value Area Range: ${value_area_range:.2f}")
        print(f"Value Area contains 70% of volume")
        print()
        
        # Show histogram sample (top 10 volume levels)
        print("TOP 10 VOLUME LEVELS:")
        print(f"{'Price':>10} {'Volume':>10} {'%':>8} {'POC':>5} {'VA':>5}")
        print("-" * 50)
        
        # Sort histogram by volume
        histogram = sorted(data['histogram'], key=lambda x: x['volume'], reverse=True)
        for bar in histogram[:10]:
            poc_marker = "POC" if bar['is_poc'] else ""
            va_marker = "VA" if bar['in_value_area'] else ""
            print(f"${bar['price']:>9.2f} {bar['volume']:>10,} {bar['volume_pct']:>7.1f}% {poc_marker:>5} {va_marker:>5}")
        
        print("=" * 60)
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False


if __name__ == "__main__":
    print("Testing Volume Profile Indicator...")
    print()
    test_volume_profile()
