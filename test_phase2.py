#!/usr/bin/env python3
"""
Phase 2 Verification Script - Test CME integration
Run after starting backend: python -m uvicorn backend.api.server:app --reload
"""

import sys
import requests
from typing import Dict, Any

# Try to import simulator
try:
    from data.cme_simulator import create_test_scenario, get_sample_cme_data
except ImportError:
    print("⚠️ Could not import cme_simulator. Make sure you're running from project root.")
    sys.exit(1)

BASE_URL = "http://localhost:8000"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, func):
        """Run a test and track results."""
        try:
            print(f"\n{name}...")
            func()
            self.passed += 1
            print(f"  ✅ PASS")
        except Exception as e:
            self.failed += 1
            print(f"  ❌ FAIL: {str(e)}")
    
    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print(f"RESULTS: {self.passed}/{total} passed")
        print("=" * 60)
        return self.failed == 0


def main():
    print("\n" + "=" * 60)
    print("🧪 PHASE 2 — CME DATA INTEGRATION TEST")
    print("=" * 60)
    
    runner = TestRunner()
    
    # Test 1: Health check
    def test_health():
        r = requests.get(f"{BASE_URL}/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "GANN" in data["engines_active"]
        print(f"    Status: {data['status']}")
        print(f"    Engines: {len(data['engines_active'])} active")
    
    runner.test("1️⃣  Health Check", test_health)
    
    # Test 2: CME Status
    def test_cme_status():
        r = requests.get(f"{BASE_URL}/api/v1/cme/status")
        assert r.status_code == 200
        data = r.json()
        assert "data_source" in data
        print(f"    Data source: {data['data_source']}")
        print(f"    Cached bars: {data['cached_bars']}")
    
    runner.test("2️⃣  CME Status Endpoint", test_cme_status)
    
    # Test 3: Ingest normal trades
    def test_ingest_normal():
        trades = create_test_scenario("normal")
        assert len(trades) > 0
        r = requests.post(f"{BASE_URL}/api/v1/cme/ingest", json=trades)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ingested"
        assert data["trades_processed"] > 0
        print(f"    Trades processed: {data['trades_processed']}")
        print(f"    Current price: ${data['current_price']}")
    
    runner.test("3️⃣  Ingest Normal Trades", test_ingest_normal)
    
    # Test 4: Ingest iceberg pattern
    def test_ingest_iceberg():
        trades = create_test_scenario("iceberg")
        assert len(trades) > 0
        r = requests.post(f"{BASE_URL}/api/v1/cme/ingest", json=trades)
        assert r.status_code == 200
        data = r.json()
        print(f"    Trades processed: {data['trades_processed']}")
        print(f"    Icebergs detected: {data['iceberg_zones_detected']}")
    
    runner.test("4️⃣  Ingest Iceberg Pattern", test_ingest_iceberg)
    
    # Test 5: Send bid/ask quote
    def test_quote():
        quote = {
            "bid_price": 2450.2,
            "ask_price": 2450.5,
            "bid_size": 250,
            "ask_size": 300,
            "timestamp": "2026-01-17T14:30:45Z"
        }
        r = requests.post(f"{BASE_URL}/api/v1/cme/quote", json=quote)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "quote_updated"
        print(f"    Bid: {data['bid']}")
        print(f"    Ask: {data['ask']}")
        print(f"    Spread: {data['spread']}")
    
    runner.test("5️⃣  Quote Update Endpoint", test_quote)
    
    # Test 6: AI Mentor v2 (with real data)
    def test_mentor_v2():
        # First ingest some data
        trades = create_test_scenario("normal")
        requests.post(f"{BASE_URL}/api/v1/cme/ingest", json=trades)
        
        # Now get mentor panel
        r = requests.post(
            f"{BASE_URL}/api/v1/mentor/v2",
            json={"symbol": "XAUUSD", "refresh": True}
        )
        assert r.status_code == 200
        data = r.json()
        assert "current_price" in data
        assert "ai_verdict" in data
        assert "confidence_percent" in data
        print(f"    Current price: ${data['current_price']}")
        print(f"    AI verdict: {data['ai_verdict']}")
        print(f"    Confidence: {data['confidence_percent']}%")
        print(f"    Iceberg detected: {data['iceberg_activity']['detected']}")
    
    runner.test("6️⃣  AI Mentor v2 Endpoint", test_mentor_v2)
    
    # Test 7: Gann levels with real data
    def test_gann_with_real():
        # Ingest iceberg to test with variety
        trades = create_test_scenario("iceberg")
        requests.post(f"{BASE_URL}/api/v1/cme/ingest", json=trades)
        
        # Now call Gann with real data
        r = requests.post(
            f"{BASE_URL}/api/v1/gann",
            json={"high": 2460, "low": 2440}
        )
        assert r.status_code == 200
        data = r.json()
        assert "levels" in data
        print(f"    Range: {data['range']}")
        print(f"    50% level: {data['levels'].get('50%')}")
        print(f"    200% level: {data['levels'].get('200%')}")
    
    runner.test("7️⃣  Gann Levels Calculation", test_gann_with_real)
    
    # Test 8: Chart data endpoint
    def test_chart():
        r = requests.post(
            f"{BASE_URL}/api/v1/chart",
            json={"symbol": "XAUUSD", "interval": "5m", "bars": 100}
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["bars"]) > 0
        print(f"    Bars generated: {len(data['bars'])}")
        print(f"    Levels: {len(data['levels'])}")
    
    runner.test("8️⃣  Chart Data Endpoint", test_chart)
    
    # Test 9: Volatile scenario
    def test_volatile_scenario():
        trades = create_test_scenario("volatile")
        r = requests.post(f"{BASE_URL}/api/v1/cme/ingest", json=trades)
        assert r.status_code == 200
        data = r.json()
        print(f"    Trades processed: {data['trades_processed']}")
        print(f"    Icebergs detected: {data['iceberg_zones_detected']}")
        assert data["iceberg_zones_detected"] > 0
    
    runner.test("9️⃣  Volatile Scenario Test", test_volatile_scenario)
    
    # Final summary
    success = runner.summary()
    
    if success:
        print("\n✅ ALL TESTS PASSED - PHASE 2 READY")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - CHECK ERRORS ABOVE")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        print("\nMake sure backend is running:")
        print("  python -m uvicorn backend.api.server:app --reload")
        sys.exit(1)
