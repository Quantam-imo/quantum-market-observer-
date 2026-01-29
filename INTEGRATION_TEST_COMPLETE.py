#!/usr/bin/env python3
"""
COMPLETE INTEGRATION TEST - Full Backend Wiring
Tests the entire Quantum Market Observer system end-to-end
All engines working together in realistic conditions

Run with: python INTEGRATION_TEST_COMPLETE.py
"""

import sys
from datetime import datetime, timedelta
import json


def generate_realistic_candles(num_candles=240, start_price=2500.0, volatility=0.8):
    """Generate synthetic but realistic OHLCV data mimicking GC (COMEX Gold)."""
    candles = []
    current_time = datetime(2025, 1, 20, 14, 0, 0)  # Start: 2025-01-20 14:00 UTC (NY session)
    close = start_price

    import random
    random.seed(42)  # Reproducible

    for i in range(num_candles):
        # Realistic price movement with slight trends
        if i % 50 == 0:
            trend = random.choice([-0.3, 0.3])  # Trend change every 50 bars
        
        direction = 1 if random.random() > 0.48 else -1
        price_move = direction * random.uniform(0.1, volatility)
        
        open_price = close
        high = open_price + random.uniform(volatility, volatility * 2)
        low = open_price - random.uniform(volatility, volatility * 2)
        close = (high + low) / 2 + price_move
        
        candle = {
            "time": current_time.isoformat(),
            "open": round(open_price, 2),
            "high": round(max(open_price, high), 2),
            "low": round(min(open_price, low), 2),
            "close": round(close, 2),
            "volume": int(random.uniform(500, 2000)),
        }
        
        candles.append(candle)
        current_time += timedelta(minutes=1)

    return candles


def test_01_core_engines():
    """TEST 1: Core market analysis engines."""
    print("\n" + "="*80)
    print("TEST 1: Core Market Analysis Engines")
    print("="*80)
    
    from backend.engines.gann import GannEngine
    from backend.engines.astro import AstroEngine
    from backend.engines.cycles import CycleEngine
    from backend.engines.bar_builder import update_bar
    
    # Test Gann
    gann = GannEngine()
    levels = gann.intraday_levels(high=2510, low=2490)
    assert "100%" in levels
    assert levels["100%"] == 2510
    print("✓ GannEngine: Levels calculated correctly")
    
    # Test Astro
    astro = AstroEngine()
    reversal = astro.is_reversal_window()
    assert isinstance(reversal, bool)
    print(f"✓ AstroEngine: Reversal window = {reversal}")
    
    # Test Cycles
    cycle = CycleEngine()
    is_cycle_21 = cycle.check(21)
    assert is_cycle_21 == True
    print("✓ CycleEngine: Cycle 21 detected")
    
    # Test Bar Builder
    bar = update_bar("GC", 2500.5, 100, "1m")
    assert bar["close"] == 2500.5
    assert bar["volume"] == 100
    print("✓ BarBuilder: 1-minute bar constructed")
    
    print("\n✅ TEST 1 PASSED: All core engines functional")


def test_02_iceberg_detection():
    """TEST 2: Institutional iceberg detection."""
    print("\n" + "="*80)
    print("TEST 2: Institutional Iceberg Detection")
    print("="*80)
    
    from backend.intelligence.absorption_engine import AbsorptionEngine
    from backend.intelligence.advanced_iceberg_engine import IcebergDetector
    from backend.engines.iceberg import IcebergEngine
    from backend.engines.iceberg_zone_engine import IcebergZoneEngine
    
    # Create absorption-like trades
    trades = [
        {"price": 2500.0, "size": 150, "side": "BUY", "timestamp": "10:00:00"},
        {"price": 2500.0, "size": 160, "side": "BUY", "timestamp": "10:01:00"},
        {"price": 2500.1, "size": 140, "side": "SELL", "timestamp": "10:02:00"},
        {"price": 2500.0, "size": 200, "side": "BUY", "timestamp": "10:03:00"},
        {"price": 2500.0, "size": 180, "side": "BUY", "timestamp": "10:04:00"},
    ]
    
    # Test Absorption Engine
    absorption = AbsorptionEngine(threshold=400)
    zones = absorption.detect(trades)
    assert len(zones) > 0
    print(f"✓ AbsorptionEngine: Detected {len(zones)} zone(s)")
    
    # Test Advanced Iceberg Detector
    detector = IcebergDetector()
    absorption_zones = detector.detect_absorption_zones(trades)
    assert len(absorption_zones) > 0
    print(f"✓ IcebergDetector: {len(absorption_zones)} absorption zone(s) detected")
    
    # Test Iceberg Zone Engine
    zone_engine = IcebergZoneEngine()
    zone = zone_engine.create_zone(xau_price=2500.0, direction="BUY", strength="A", session="NEW_YORK")
    assert zone["direction"] == "BUY"
    assert zone["top"] == 2503.0  # 3.0 pip height for "A"
    print(f"✓ IcebergZoneEngine: Zone created {zone['bottom']}-{zone['top']}")
    
    print("\n✅ TEST 2 PASSED: Iceberg detection working")


def test_03_liquidity_analysis():
    """TEST 3: Liquidity and orderflow analysis."""
    print("\n" + "="*80)
    print("TEST 3: Liquidity & OrderFlow Analysis")
    print("="*80)
    
    from backend.intelligence.liquidity_sweep_engine import LiquiditySweepEngine
    from backend.engines.orderflow_engine import OrderFlowEngine
    import time
    
    # Test Sweep Detection
    candles = [
        {"time": "10:00", "high": 2510, "low": 2490, "open": 2505, "close": 2495, "volume": 1000},
        {"time": "10:01", "high": 2515, "low": 2505, "open": 2510, "close": 2505, "volume": 1200},  # Wick up, close down = sweep
        {"time": "10:02", "high": 2510, "low": 2500, "open": 2505, "close": 2502, "volume": 900},
    ]
    
    sweep_engine = LiquiditySweepEngine()
    sweeps = sweep_engine.detect(candles)
    assert len(sweeps) > 0
    print(f"✓ SweepEngine: Detected {len(sweeps)} sweep(s)")
    
    # Test OrderFlow Engine
    of_engine = OrderFlowEngine()
    current_time = int(time.time())
    
    trades = [
        {"price": 2500.0, "size": 200, "side": "BUY", "timestamp": current_time},
        {"price": 2500.5, "size": 150, "side": "BUY", "timestamp": current_time},
        {"price": 2500.2, "size": 100, "side": "SELL", "timestamp": current_time},
    ]
    
    for trade in trades:
        of_engine.update(trade)
    
    snapshot = of_engine.snapshot()
    assert snapshot["delta"] > 0
    assert snapshot["bias"] == "BUY"
    print(f"✓ OrderFlowEngine: Delta={snapshot['delta']}, Bias={snapshot['bias']}")
    
    print("\n✅ TEST 3 PASSED: Liquidity analysis working")


def test_04_confidence_scoring():
    """TEST 4: Multi-pillar confidence scoring."""
    print("\n" + "="*80)
    print("TEST 4: Confidence Scoring System")
    print("="*80)
    
    from backend.intelligence.confidence_engine import ConfidenceEngine as IntelConfidence
    from backend.mentor.confidence_engine import ConfidenceEngine as MentorConfidence
    
    # Test Intelligence Confidence (5-pillar)
    intel_conf = IntelConfidence()
    
    # Build context with all pillars
    qmo_ctx = {"trend": True, "expansion": True}
    liquidity_ctx = {"sweep": True, "rejection": True}
    iceberg_ctx = {"historical_absorption": True, "same_price": True}
    execution_ctx = {"tight_stop": True, "clear_invalidation": True}
    timing_ctx = {"session_open": True}
    
    result = intel_conf.compute_confidence(qmo_ctx, liquidity_ctx, iceberg_ctx, execution_ctx, timing_ctx)
    assert result["total"] > 0
    print(f"✓ IntelligenceConfidence: Total={result['total']}, Breakdown: QMO={result['qmo']}, IMO={result['imo']}")
    
    # Test Mentor Confidence (weighted average)
    mentor_conf = MentorConfidence()
    scores = {
        "QMO": 0.80,
        "IMO": 0.85,
        "GANN": 0.75,
        "ASTRO": 0.70,
        "CYCLE": 0.65
    }
    final_score = mentor_conf.score(scores)
    assert 0 <= final_score <= 1
    print(f"✓ MentorConfidence: Weighted score = {final_score:.2f}")
    
    print("\n✅ TEST 4 PASSED: Confidence scoring operational")


def test_05_signal_filtering():
    """TEST 5: Signal quality filtering."""
    print("\n" + "="*80)
    print("TEST 5: Signal Quality Filters")
    print("="*80)
    
    from backtesting.replay_filters import ReplayFilters
    
    filters = ReplayFilters()
    
    # Test: High-quality signal (should pass)
    context_good = {
        "session": "LONDON",
        "killzone": False,
        "news": {"active": False},
        "iceberg_score": 0.75,
        "confidence": 0.80
    }
    assert filters.allow_signal(context_good) == True
    print("✓ Filter: High-quality signal PASSED")
    
    # Test: Low confidence (should fail)
    context_low_conf = {
        "session": "LONDON",
        "killzone": False,
        "news": {"active": False},
        "iceberg_score": 0.75,
        "confidence": 0.50  # Below min_confidence
    }
    assert filters.allow_signal(context_low_conf) == False
    print("✓ Filter: Low-confidence signal BLOCKED")
    
    # Test: In killzone (should fail)
    context_killzone = {
        "session": "LONDON",
        "killzone": True,  # During NY morning spike
        "news": {"active": False},
        "iceberg_score": 0.75,
        "confidence": 0.80
    }
    assert filters.allow_signal(context_killzone) == False
    print("✓ Filter: Killzone signal BLOCKED")
    
    # Test: High-impact news (should fail)
    context_news = {
        "session": "NEW_YORK",
        "killzone": False,
        "news": {"active": True, "impact": "HIGH"},  # NFP/FOMC window
        "iceberg_score": 0.75,
        "confidence": 0.80
    }
    assert filters.allow_signal(context_news) == False
    print("✓ Filter: High-impact news signal BLOCKED")
    
    print("\n✅ TEST 5 PASSED: All filters operational")


def test_06_session_context():
    """TEST 6: Session awareness and risk management."""
    print("\n" + "="*80)
    print("TEST 6: Session Context & Risk Management")
    print("="*80)
    
    from backtesting.session_engine import SessionEngine
    from backend.risk.position_sizer import PositionSizer
    from backend.intelligence.capital_protection_engine import CapitalProtectionEngine
    
    # Test Session Detection
    from datetime import datetime
    session_engine = SessionEngine()
    
    times_and_sessions = [
        (datetime(2025, 1, 20, 2, 0), "ASIA"),      # 02:00 UTC = Asia
        (datetime(2025, 1, 20, 9, 0), "LONDON"),    # 09:00 UTC = London
        (datetime(2025, 1, 20, 15, 0), "NEW_YORK"), # 15:00 UTC = NY
        (datetime(2025, 1, 20, 22, 30), "OFF_SESSION"),  # 22:30 UTC = Off
    ]
    
    for dt, expected_session in times_and_sessions:
        session = session_engine.get_session(dt)
        assert session == expected_session
    print(f"✓ SessionEngine: All 4 sessions identified correctly")
    
    # Test Position Sizing
    sizer = PositionSizer()
    lot_size = sizer.calculate_lot_size(
        balance=10000,
        risk_percent=0.5,  # 0.5% risk
        stop_loss_pips=20,
        pip_value=10,
        volatility="normal"
    )
    assert lot_size > 0
    print(f"✓ PositionSizer: Calculated lot size = {lot_size:.2f}")
    
    # Test Capital Protection
    cap_protect = CapitalProtectionEngine(account_size=10000)
    cap_protect.record_trade(pnl=100)  # +100 PnL
    cap_protect.record_trade(pnl=-50)   # -50 PnL
    cap_protect.record_trade(pnl=-80)   # -80 PnL (2nd loss)
    
    status = cap_protect.get_protection_status()
    assert status["session_losses"] == 2
    print(f"✓ CapitalProtection: Session locked after {status['session_losses']} losses")
    
    print("\n✅ TEST 6 PASSED: Session management operational")


def test_07_trader_progression():
    """TEST 7: Trader progression engine."""
    print("\n" + "="*80)
    print("TEST 7: Trader Progression System")
    print("="*80)
    
    from backend.mentor.progression_engine import ProgressionEngine
    from backend.pricing.tier_system import SubscriptionTier
    from backend.pricing.feature_gate import FeatureGate
    
    # Create beginner trader
    progression = ProgressionEngine()
    
    # Log some trades
    for i in range(5):
        progression.log_trade({
            "result": "WIN" if i % 2 == 0 else "LOSS",
            "followed_rules": True,
            "emotion": "CALM",
            "r_multiple": 1.0 if i % 2 == 0 else -0.5
        })
    
    assert progression.current_phase.name == "BEGINNER"
    print(f"✓ Progression: Current phase = {progression.current_phase.name}")
    
    features = progression.get_phase_features()
    assert features["live_signals"] == True
    assert features["gann_levels"] == False
    print(f"✓ Progression: Beginner has {sum(features.values())} features unlocked")
    
    # Test Feature Gate (pricing integration)
    gate = FeatureGate(SubscriptionTier.BASIC, progression.current_phase)
    assert gate.can_access("live_signals") == True
    assert gate.can_access("api_access") == False
    print(f"✓ FeatureGate: BASIC + Beginner tier restrictions applied")
    
    print("\n✅ TEST 7 PASSED: Progression system working")


def test_08_replay_pipeline():
    """TEST 8: Complete replay backtesting pipeline."""
    print("\n" + "="*80)
    print("TEST 8: Replay Pipeline (Backtesting)")
    print("="*80)
    
    from backtesting.ai_snapshot import AISnapshotStore
    from backtesting.timeline_builder import TimelineBuilder
    from backtesting.chart_packet_builder import ChartPacketBuilder
    from backtesting.explanation_engine import ExplanationEngine
    
    # Generate test data
    candles = generate_realistic_candles(num_candles=50)
    
    # Test AISnapshotStore
    snapshot_store = AISnapshotStore()
    for i, candle in enumerate(candles[:10]):
        context = {
            "qmo": {"phase": "ACCUMULATION"},
            "liquidity": {"type": "SWEEP"},
            "gann": {"level": 2500.0},
            "astro": {"window": "active"},
            "cycle": {"bar": i},
        }
        decision = {"action": "BUY", "confidence": 0.75} if i % 3 == 0 else None
        snapshot_store.store(candle, context, decision)
    
    stats = snapshot_store.count()
    assert stats["total_candles"] == 10
    print(f"✓ AISnapshotStore: Stored {stats['total_candles']} candles, {stats['signals']} signals")
    
    # Test TimelineBuilder
    timeline = TimelineBuilder()
    for i, candle in enumerate(candles[:10]):
        context = {
            "session": "NEW_YORK",
            "killzone": False,
            "news": {"active": False},
            "iceberg_score": 0.6 + (i * 0.02),
            "confidence": 0.70
        }
        decision = {"action": "SELL", "confidence": 0.82} if i % 5 == 0 else None
        explanation = {"summary": f"Candle {i}", "details": []}
        timeline.record(candle, context, decision, explanation)
    
    timeline_export = timeline.export()
    assert len(timeline_export) == 10
    print(f"✓ TimelineBuilder: Timeline has {len(timeline_export)} entries")
    
    # Test ChartPacketBuilder
    packet_builder = ChartPacketBuilder()
    for candle in candles[:10]:
        context = {"session": "NEW_YORK", "killzone": False, "iceberg_score": 0.65}
        decision = {"action": "BUY", "confidence": 0.78}
        packet_builder.record(candle, context, decision)
    
    packets = packet_builder.export()
    assert len(packets) == 10
    print(f"✓ ChartPacketBuilder: Created {len(packets)} chart packets")
    
    # Test ExplanationEngine
    explainer = ExplanationEngine()
    context = {"session": "LONDON", "killzone": False, "news": {"active": False}, "confidence": 0.85}
    decision = {"action": "BUY", "confidence": 0.85}
    explanation = explainer.build(context, decision)
    assert explanation["summary"] is not None
    print(f"✓ ExplanationEngine: Generated explanation")
    
    print("\n✅ TEST 8 PASSED: Replay pipeline operational")


def test_09_end_to_end_integration():
    """TEST 9: Full end-to-end system integration."""
    print("\n" + "="*80)
    print("TEST 9: Complete End-to-End Integration")
    print("="*80)
    
    from backend.intelligence.step3_imo_pipeline import Step3IMOPipeline
    from backend.mentor.mentor_brain import MentorBrain
    
    # Create pipeline
    pipeline = Step3IMOPipeline()
    mentor = MentorBrain(account_size=10000)
    
    # Generate realistic data
    trades = [
        {"price": 2500.0, "size": 150, "side": "BUY", "timestamp": "10:00:00"},
        {"price": 2500.0, "size": 160, "side": "BUY", "timestamp": "10:01:00"},
        {"price": 2500.1, "size": 140, "side": "SELL", "timestamp": "10:02:00"},
    ]
    
    candles = [
        {"time": "10:00", "open": 2500, "high": 2505, "low": 2495, "close": 2502, "volume": 1000},
        {"time": "10:01", "open": 2502, "high": 2508, "low": 2501, "close": 2507, "volume": 1200},
        {"time": "10:02", "open": 2507, "high": 2510, "low": 2506, "close": 2503, "volume": 900},
    ]
    
    # Process through pipeline
    decision = pipeline.process_tick(trades, candles)
    assert decision is not None
    assert "decision" in decision
    print(f"✓ IMOPipeline: Generated decision: {decision['decision']}")
    
    # Get institutional signal
    signal = pipeline.get_institutional_signal()
    assert signal is not None
    print(f"✓ IMOPipeline: Confidence = {signal['confidence']:.2f}")
    
    # Record trade result through mentor
    mentor.record_trade_result(
        setup_type="iceberg",
        win=True,
        pnl=150.0,
        follow_through_pips=45.0,
        session="LONDON"
    )
    
    # Get adaptive status
    status = mentor.get_adaptive_status()
    assert "edge_decay" in status
    assert "capital_protection" in status
    print(f"✓ MentorBrain: Adaptive engines tracking performance")
    
    print("\n✅ TEST 9 PASSED: Full integration successful")


def run_all_tests():
    """Execute all integration tests."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "QUANTUM MARKET OBSERVER" + " "*36 + "║")
    print("║" + " "*18 + "COMPLETE INTEGRATION TEST SUITE" + " "*29 + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("Core Engines", test_01_core_engines),
        ("Iceberg Detection", test_02_iceberg_detection),
        ("Liquidity Analysis", test_03_liquidity_analysis),
        ("Confidence Scoring", test_04_confidence_scoring),
        ("Signal Filtering", test_05_signal_filtering),
        ("Session Management", test_06_session_context),
        ("Trader Progression", test_07_trader_progression),
        ("Replay Pipeline", test_08_replay_pipeline),
        ("End-to-End Integration", test_09_end_to_end_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSING! System is fully integrated and operational.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) need attention.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
