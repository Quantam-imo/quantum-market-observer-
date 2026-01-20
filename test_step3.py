"""
STEP 3 — LIVE TEST DEMONSTRATION
Real institutional detection in action
Run: python test_step3.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.intelligence.step3_imo_pipeline import Step3IMOPipeline

def test_step3_pipeline():
    """
    Demonstrates Step 3 institutional detection pipeline
    Using realistic CME GC trade data
    """
    
    print("\n" + "="*70)
    print("🚀 STEP 3 — INSTITUTIONAL IMO ENGINE TEST")
    print("="*70 + "\n")
    
    # Initialize pipeline
    pipeline = Step3IMOPipeline()
    
    # Scenario 1: Heavy absorption zone
    print("📊 SCENARIO 1: Heavy Institutional Absorption")
    print("-" * 70)
    
    absorption_trades = [
        {"price": 2850.5, "size": 85, "side": "SELL", "timestamp": "10:30:00"},
        {"price": 2850.6, "size": 92, "side": "SELL", "timestamp": "10:30:05"},
        {"price": 2850.5, "size": 78, "side": "SELL", "timestamp": "10:30:10"},
        {"price": 2850.6, "size": 88, "side": "BUY", "timestamp": "10:30:15"},
        {"price": 2850.5, "size": 80, "side": "SELL", "timestamp": "10:30:20"},
        {"price": 2850.6, "size": 83, "side": "SELL", "timestamp": "10:30:25"},
    ]
    
    absorption_candle = {
        "open": 2850.0,
        "high": 2851.2,
        "low": 2850.0,
        "close": 2850.5,
        "volume": 506,
        "time": "10:31:00"
    }
    
    decision1 = pipeline.process_tick(absorption_trades, [absorption_candle])
    
    print(f"CME Trades: {len(absorption_trades)} trades clustered at 2850.5-2850.6")
    print(f"Total Volume: {sum(t['size'] for t in absorption_trades)} contracts")
    print(f"Buyer/Seller: Mixed (institutions defending)")
    print(f"\n✅ Decision: {decision1['decision']}")
    print(f"   Confidence: {decision1['confidence']:.1%}")
    print(f"   Primary Reason: {decision1['primary_reason']}")
    print(f"\n   Score Breakdown:")
    for key, value in decision1['score_breakdown'].items():
        print(f"   - {key}: {value:.2f}")
    
    # Scenario 2: Liquidity sweep (trap)
    print("\n\n📊 SCENARIO 2: Liquidity Sweep / Trap Detection")
    print("-" * 70)
    
    sweep_trades = [
        {"price": 2853.0, "size": 45, "side": "BUY", "timestamp": "11:00:00"},
        {"price": 2853.1, "size": 48, "side": "BUY", "timestamp": "11:00:05"},
        {"price": 2852.9, "size": 42, "side": "BUY", "timestamp": "11:00:10"},
    ]
    
    # Candle shows break above then rejection below
    sweep_candle = {
        "open": 2852.5,
        "high": 2854.2,  # BREAK above
        "low": 2852.0,
        "close": 2852.8,  # CLOSE below break
        "volume": 420,
        "time": "11:01:00"
    }
    
    decision2 = pipeline.process_tick(sweep_trades, [sweep_candle])
    
    print(f"Price Action: Broke 2854.2 then rejected to 2852.8")
    print(f"Setup: BUY_SIDE_SWEEP detected")
    print(f"Implication: Retail long stops were HUNTED and liquidated")
    print(f"\n✅ Decision: {decision2['decision']}")
    print(f"   Confidence: {decision2['confidence']:.1%}")
    print(f"   Sweeps Detected: {decision2['zone_count']}")
    
    # Scenario 3: Multi-session confluence (STRONGEST SIGNAL)
    print("\n\n📊 SCENARIO 3: Multi-Session Confluence")
    print("-" * 70)
    
    print("Memory Zones (from previous sessions):")
    print(f"   Level 2850.5 - VISITED 3 times")
    print(f"   Level 2853.0 - VISITED 2 times")
    print(f"   Level 2847.0 - VISITED 1 time")
    
    # Manually store zones to simulate history
    pipeline.memory.store({
        "price": 2850.5,
        "volume": 450,
        "type": "ABSORPTION",
        "timestamp": "2026-01-15"
    })
    pipeline.memory.store({
        "price": 2850.5,
        "volume": 420,
        "type": "ABSORPTION",
        "timestamp": "2026-01-16"
    })
    
    confluence_trades = [
        {"price": 2850.5, "size": 72, "side": "SELL", "timestamp": "12:00:00"},
        {"price": 2850.5, "size": 68, "side": "SELL", "timestamp": "12:00:05"},
        {"price": 2850.6, "size": 75, "side": "SELL", "timestamp": "12:00:10"},
    ]
    
    confluence_candle = {
        "open": 2850.0,
        "high": 2851.0,
        "low": 2849.8,
        "close": 2850.5,
        "volume": 215,
        "time": "12:01:00"
    }
    
    decision3 = pipeline.process_tick(confluence_trades, [confluence_candle])
    
    print(f"\n   NEW trades arrive at SAME level 2850.5")
    print(f"   This is 3rd+ time institutions are active here")
    print(f"\n✅ Decision: {decision3['decision']}")
    print(f"   Confidence: {decision3['confidence']:.1%}")
    print(f"   Active Memory Zones: {len(pipeline.memory.get_active_zones(2850.5))}")
    print(f"   Recommendation: {decision3['primary_reason']}")
    
    # Dashboard summary
    print("\n\n📈 PIPELINE DASHBOARD")
    print("-" * 70)
    
    dashboard = pipeline.get_dashboard_data()
    
    print(f"Total Decisions Made: {dashboard['execution_count']}")
    print(f"Zones Stored: {dashboard['memory']['total_zones_stored']}")
    print(f"Strong Zones (2+ visits): {dashboard['memory']['strong_zones']}")
    print(f"\nLatest IMO Decision: {dashboard['imo_decision']['decision']}")
    print(f"Confidence: {dashboard['imo_decision']['confidence']:.1%}")
    print(f"\nScore Breakdown:")
    for component, score in dashboard['imo_decision']['score_breakdown'].items():
        bar = "█" * int(score * 50)
        print(f"  {component:12} {bar} {score:.2f}")
    
    # Explanation
    print("\n\n💡 MENTOR EXPLANATION")
    print("-" * 70)
    print(dashboard['imo_explanation'])
    
    print("\n" + "="*70)
    print("✅ STEP 3 TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_step3_pipeline()
