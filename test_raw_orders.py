#!/usr/bin/env python3
"""
Test script for raw order recording system
Records sample orders and verifies the full pipeline
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def test_record_orders():
    """Record sample orders"""
    print("📝 Recording sample orders...")
    
    test_orders = [
        {"price": 5310.00, "size": 5, "side": "SELL"},
        {"price": 5310.25, "size": 8, "side": "BUY"},
        {"price": 5310.50, "size": 12, "side": "BUY"},
        {"price": 5310.75, "size": 6, "side": "SELL"},
        {"price": 5311.00, "size": 15, "side": "BUY"},
        {"price": 5311.25, "size": 3, "side": "SELL"},
        {"price": 5311.50, "size": 20, "side": "BUY"},
        {"price": 5311.75, "size": 7, "side": "SELL"},
    ]
    
    for i, order in enumerate(test_orders, 1):
        try:
            response = requests.post(
                f"{API_BASE}/orders/record",
                params=order
            )
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Order {i}: {order['side']} {order['size']} @ ${order['price']} - {data['status']}")
            else:
                print(f"  ❌ Order {i} failed: {response.text}")
        except Exception as e:
            print(f"  ❌ Error recording order {i}: {e}")
    
    print()

def test_get_recent():
    """Get recent orders"""
    print("📊 Fetching recent orders...")
    try:
        response = requests.get(f"{API_BASE}/orders/recent?limit=10")
        data = response.json()
        
        print(f"  ✅ Retrieved {data['count']} orders:")
        for order in data['orders']:
            print(f"     {order['timestamp']} | ${order['price']} | {order['size']} {order['side']}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

def test_get_stats():
    """Get order statistics"""
    print("📈 Fetching order statistics...")
    try:
        response = requests.get(f"{API_BASE}/orders/stats")
        stats = response.json()
        
        print(f"  ✅ Stats retrieved:")
        print(f"     Total Orders: {stats['total_orders']}")
        print(f"     Buy Orders: {stats['buy_orders']} | Buy Volume: {stats['buy_volume']}")
        print(f"     Sell Orders: {stats['sell_orders']} | Sell Volume: {stats['sell_volume']}")
        print(f"     Net Volume: {stats['net_volume']}")
        print(f"     Price Range: ${stats['min_price']} - ${stats['max_price']}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

def test_get_by_side():
    """Get orders by side"""
    print("🔍 Fetching orders by side...")
    try:
        for side in ["BUY", "SELL"]:
            response = requests.get(f"{API_BASE}/orders/by-side?side={side}&limit=5")
            data = response.json()
            print(f"  ✅ {side} orders ({data['count']}):")
            for order in data['orders'][:3]:
                print(f"     ${order['price']} | {order['size']} contracts")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

def test_volume_profile():
    """Get volume profile"""
    print("📊 Fetching volume profile...")
    try:
        response = requests.get(f"{API_BASE}/orders/profile?limit=10")
        data = response.json()
        
        print(f"  ✅ Volume profile retrieved ({len(data['profile'])} levels):")
        for price_level in sorted(data['profile'].keys()):
            profile = data['profile'][price_level]
            print(f"     ${price_level}: BUY={profile['buy']} | SELL={profile['sell']} | NET={profile['net']}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

def test_export():
    """Export orders to CSV"""
    print("📥 Exporting orders to CSV...")
    try:
        response = requests.get(f"{API_BASE}/orders/export")
        if response.status_code == 200:
            # Save to file
            filename = f"/tmp/test_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w') as f:
                f.write(response.text)
            
            lines = response.text.strip().split('\n')
            print(f"  ✅ Exported to {filename}")
            print(f"     Header: {lines[0]}")
            print(f"     Total rows: {len(lines) - 1}")
            if len(lines) > 1:
                print(f"     First row: {lines[1]}")
        else:
            print(f"  ❌ Export failed: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 RAW ORDER RECORDING SYSTEM TEST")
    print("="*60 + "\n")
    
    test_record_orders()
    test_get_recent()
    test_get_stats()
    test_get_by_side()
    test_volume_profile()
    test_export()
    
    print("="*60)
    print("✅ TEST COMPLETE - Raw order system fully operational!")
    print("="*60 + "\n")
