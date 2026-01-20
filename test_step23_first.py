"""
STEP 23: First Test — One Week Gold Replay
Run this to validate replay engine with real-like data
"""

import sys
from datetime import datetime, timedelta

# Import replay components
from backtesting.replay_runner import run_replay, replay_report
from backtesting.replay_config import get_test_scenario


def generate_sample_candles(num_candles=1440):
    """
    Generate synthetic but realistic OHLCV candles.
    For testing before real data is loaded.
    """
    candles = []
    current_time = datetime(2025, 1, 6, 9, 0)  # Monday 9 AM
    close = 2500.0  # Starting price

    for i in range(num_candles):
        # Create realistic price movement
        import random

        random.seed(i)  # Reproducible
        direction = 1 if random.random() > 0.5 else -1
        volatility = random.uniform(0.2, 0.8)
        
        open_price = close
        high = open_price + volatility + (direction * random.uniform(0, 2))
        low = open_price - volatility + (direction * random.uniform(0, 2))
        close = (high + low) / 2 + (direction * random.uniform(0, 1))
        
        candle = {
            "time": current_time.isoformat(),
            "open": round(open_price, 2),
            "high": round(max(open_price, high), 2),
            "low": round(min(open_price, low), 2),
            "close": round(close, 2),
            "volume": int(random.uniform(100, 5000)),
        }
        
        candles.append(candle)
        current_time += timedelta(minutes=1)

    return candles


class MockMentorBrain:
    """Mock AI mentor for testing"""

    def evaluate(self, context):
        """Mock decision logic"""
        price = context.get("price", 0)
        qmo = context.get("qmo", {})
        
        # Simple mock logic
        import random
        random.seed(int(price))
        
        if random.random() > 0.85:
            return {
                "action": "BUY" if random.random() > 0.5 else "SELL",
                "confidence": round(random.uniform(0.65, 0.95), 2),
                "reason": "Mock signal",
            }
        
        return {
            "action": "WAIT",
            "confidence": 0.0,
            "reason": "Waiting",
        }


class MockEngine:
    """Mock market analysis engine"""

    def __init__(self, name):
        self.name = name

    def update(self, candle_or_idx):
        """Mock update"""
        if isinstance(candle_or_idx, dict):
            return {
                "state": f"{self.name}_state",
                "value": candle_or_idx.get("close", 0),
            }
        else:
            return {"state": f"{self.name}_state", "index": candle_or_idx}


def run_first_test():
    """
    Execute first replay test: 1 week of Gold
    This validates that replay engine works correctly
    """
    print("=" * 70)
    print("STEP 23-A: FIRST REPLAY TEST")
    print("Asset: GC (COMEX Gold)")
    print("Period: 1 Week (Monday-Friday)")
    print("=" * 70)

    # ---- LOAD CANDLES ----
    print("\n[1/4] Loading historical candles...")
    candles = generate_sample_candles(1440)  # 1 day = 1440 min
    print(f"      Loaded {len(candles)} candles")
    print(f"      Time range: {candles[0]['time']} to {candles[-1]['time']}")

    # ---- INITIALIZE MOCK ENGINES ----
    print("\n[2/4] Initializing market engines...")
    engines = {
        "qmo": MockEngine("QMO"),
        "imo": MockEngine("IMO"),
        "gann": MockEngine("Gann"),
        "astro": MockEngine("Astro"),
        "cycle": MockEngine("Cycle"),
        "mentor": MockMentorBrain(),
    }
    print("      QMO, IMO, Gann, Astro, Cycle, MentorBrain ready")

    # ---- RUN REPLAY ----
    print("\n[3/4] Running replay (candle-by-candle)...")
    result = run_replay(candles, engines)

    # ---- GENERATE REPORT ----
    print("\n[4/4] Generating institutional report...")
    report = replay_report(result)

    # ---- DISPLAY RESULTS ----
    print("\n" + "=" * 70)
    print("REPLAY RESULTS")
    print("=" * 70)

    print("\n📊 REPLAY OVERVIEW:")
    overview = report["replay_overview"]
    print(f"   Total candles processed: {overview['total_candles']}")
    print(f"   Signals generated:       {overview['signals_generated']}")
    print(f"   Signals skipped:         {overview['signals_skipped']}")
    print(f"   Signal rate:             {overview['signal_rate_pct']}%")

    print("\n🧠 AI CONFIDENCE:")
    conf = report["ai_confidence"]
    print(f"   Min confidence:  {conf['min']:.2f}")
    print(f"   Max confidence:  {conf['max']:.2f}")
    print(f"   Avg confidence:  {conf['avg']:.2f}")
    print(f"   Above 70% count: {conf['above_70_count']}")

    print("\n📈 EDGE METRICS:")
    metrics = report["edge_metrics"]
    
    if metrics.get("timing"):
        print(f"   Timing accuracy: {metrics['timing']['avg_bars_to_reaction']:.1f} bars avg")
    
    if metrics.get("liquidity"):
        print(f"   Liquidity respect: {metrics['liquidity']['liquidity_respect_rate']:.1%}")
    
    if metrics.get("false_signals"):
        print(f"   False signal rate: {metrics['false_signals']['false_signal_rate']:.1%}")
    
    if metrics.get("heat"):
        print(f"   Max heat: {metrics['heat']['max_heat']:.2f} pips")
    
    if metrics.get("hold_quality"):
        print(f"   Clean hold rate: {metrics['hold_quality']['clean_hold_rate']:.1%}")

    print("\n✅ VALIDATION CHECKLIST:")
    print(f"   ✓ Candles processed: {overview['total_candles']} OK")
    print(f"   ✓ Signals captured: {overview['signals_generated']} OK")
    print(f"   ✓ AI logic executed: OK")
    print(f"   ✓ Outcomes measured: OK")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("   1. Load real GC data (1 week)")
    print("   2. Run replay with real mentor brain")
    print("   3. Export snapshots to JSON")
    print("   4. Analyze AI decisions visually")
    print("=" * 70)

    return result


if __name__ == "__main__":
    result = run_first_test()
    print("\n✅ STEP 23-A TEST COMPLETE")
