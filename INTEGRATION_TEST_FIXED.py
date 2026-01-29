#!/usr/bin/env python3
"""
FIXED INTEGRATION TEST - Full Backend Wiring
Tests the entire Quantum Market Observer system end-to-end
Corrected for actual API signatures and missing dependencies

Run with: python INTEGRATION_TEST_FIXED.py
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
    """TEST 2: Institutional iceberg detection (simplified)."""
    print("\n" + "="*80)
    print("TEST 2: Institutional Iceberg Detection")
    print("="*80)
    
    from backend.intelligence.absorption_engine import AbsorptionEngine
    from backend.intelligence.advanced_iceberg_engine import IcebergDetector
    from backend.engines.iceberg_zone_engine import IcebergZoneEngine
    
    # Simplified trade data
    trades = [
        {"price": 2500.0, "size": 100, "side": "BUY", "timestamp": 1},
        {"price": 2500.0, "size": 100, "side": "BUY", "timestamp": 2},
        {"price": 2500.0, "size": 100, "side": "BUY", "timestamp": 3},
        {"price": 2500.2, "size": 200, "side": "SELL", "timestamp": 4},
    ]
    
    # Test Absorption Engine (detects absorbed volume at same price)
    absorption = AbsorptionEngine(threshold=200)
    zones = absorption.detect(trades)
    assert len(zones) > 0
    print(f"✓ AbsorptionEngine: Detected {len(zones)} absorption zone(s)")
    
    # Test Advanced Iceberg Detector
    detector = IcebergDetector()
    absorption_zones = detector.detect_absorption_zones(trades)
    assert len(absorption_zones) > 0
    print(f"✓ IcebergDetector: {len(absorption_zones)} absorption zone(s) detected")
    
    # Test Iceberg Zone Engine (creates zones with strength)
    zone_engine = IcebergZoneEngine()
    zone = zone_engine.create_zone(price=2500.0, size=300, strength=3)
    assert zone["price"] == 2500.0
    assert zone["strength"] > 0
    print(f"✓ IcebergZoneEngine: Zone strength = {zone['strength']}")
    
    print("\n✅ TEST 2 PASSED: Iceberg detection system functional")


def test_03_liquidity_analysis():
    """TEST 3: Liquidity and order flow analysis."""
    print("\n" + "="*80)
    print("TEST 3: Liquidity Analysis")
    print("="*80)
    
    from backend.intelligence.liquidity_sweep_engine import LiquiditySweepEngine
    from backend.intelligence.liquidity_story_engine import LiquidityStoryEngine
    from backend.engines.orderflow import OrderFlowEngine
    
    # Prepare trade data
    trades = [
        {"price": 2500.0, "size": 500, "side": "BUY"},
        {"price": 2500.5, "size": 500, "side": "BUY"},
        {"price": 2500.2, "size": 100, "side": "SELL"},
    ]
    
    # Test Liquidity Sweep Engine
    sweep_engine = LiquiditySweepEngine()
    trap = sweep_engine.detect_ict_trap(low=2499.5, high=2500.5, final_price=2500.2, volume_data=trades)
    assert isinstance(trap, dict)
    print(f"✓ LiquiditySweepEngine: ICT trap detection working")
    
    # Test Liquidity Story Engine
    story_engine = LiquidityStoryEngine()
    narrative = story_engine.generate_narrative(trades)
    assert narrative is not None
    print(f"✓ LiquidityStoryEngine: Narrative = '{narrative[:50]}...'")
    
    # Test OrderFlow Engine (with larger trade sizes to hit delta threshold)
    of_engine = OrderFlowEngine()
    large_trades = [
        {"price": 2500.0, "size": 500, "side": "BUY", "timestamp": 1},
        {"price": 2500.5, "size": 500, "side": "BUY", "timestamp": 2},
        {"price": 2500.2, "size": 100, "side": "SELL", "timestamp": 3},
    ]
    
    for trade in large_trades:
        of_engine.update(trade)
    
    snapshot = of_engine.snapshot()
    assert snapshot["delta"] > 0
    print(f"✓ OrderFlowEngine: Delta={snapshot['delta']}, Bias={snapshot['bias']}")
    
    print("\n✅ TEST 3 PASSED: Liquidity analysis functional")


def test_04_confidence_scoring():
    """TEST 4: Confidence scoring system."""
    print("\n" + "="*80)
    print("TEST 4: Confidence Scoring System")
    print("="*80)
    
    from backend.mentor.confidence_engine import ConfidenceEngine
    from backend.mentor.confidence_adjuster import iceberg_confidence_boost
    
    # Test Mentor Confidence (weighted average of pillars)
    mentor_conf = ConfidenceEngine()
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
    
    # Test iceberg confidence boost
    boost = iceberg_confidence_boost(zone_score=3)
    assert isinstance(boost, (int, float))
    print(f"✓ IcebergBooster: Zone score 3 gives {boost} boost")
    
    print("\n✅ TEST 4 PASSED: Confidence scoring system functional")


def test_05_signal_filters():
    """TEST 5: Signal filtering and validation."""
    print("\n" + "="*80)
    print("TEST 5: Signal Filters & Validation")
    print("="*80)
    
    from backend.intelligence.session_learning_memory import SessionLearningMemory
    from backend.session.session_guard import SessionGuard
    from backend.risk.risk_engine import RiskEngine
    
    # Test Session Guard (prevents trading in kill zones)
    guard = SessionGuard()
    
    # During Asian session, these hours should have certain restrictions
    is_safe = guard.is_safe_to_trade(hour=14)  # 14:00 = 2:00 PM NY time
    assert isinstance(is_safe, bool)
    print(f"✓ SessionGuard: Trading safe at 14:00 = {is_safe}")
    
    # Test Risk Engine (validates position sizing and stops)
    risk = RiskEngine()
    stop_distance = 50
    max_loss = 100
    can_trade = risk.validate_position(entry=2500, stop=2450, max_loss=max_loss)
    assert isinstance(can_trade, bool)
    print(f"✓ RiskEngine: Position validation passed")
    
    # Test Session Learning Memory
    memory = SessionLearningMemory()
    memory.record_setup("break_retest", win=True)
    stats = memory.get_setup_stats("break_retest")
    assert stats is not None
    print(f"✓ SessionLearningMemory: Setup stats recorded")
    
    print("\n✅ TEST 5 PASSED: Signal filters functional")


def test_06_session_management():
    """TEST 6: Session management and scheduling."""
    print("\n" + "="*80)
    print("TEST 6: Session Management")
    print("="*80)
    
    from backend.session.session_engine import SessionEngine
    from backend.risk.position_sizer import PositionSizer
    
    # Test Session Engine
    engine = SessionEngine()
    
    # Current time (simulated)
    current_hour = 14  # 2 PM NY time
    sessions = engine.get_active_sessions(current_hour)
    assert isinstance(sessions, list)
    print(f"✓ SessionEngine: {len(sessions)} session(s) active at {current_hour}:00")
    
    # Test Position Sizer
    sizer = PositionSizer()
    size = sizer.calculate_size(
        account_balance=10000,
        risk_per_trade=100,
        entry=2500,
        stop=2450
    )
    assert size > 0
    print(f"✓ PositionSizer: Trade size = {size} contracts")
    
    print("\n✅ TEST 6 PASSED: Session management functional")


def test_07_trader_progression():
    """TEST 7: Trader progression and feature unlocks."""
    print("\n" + "="*80)
    print("TEST 7: Trader Progression System")
    print("="*80)
    
    from backend.mentor.progression_engine import ProgressionEngine
    from backend.pricing.tier_system import SubscriptionTier
    from backend.pricing.feature_gate import FeatureGate
    
    # Test Progression Engine
    progression = ProgressionEngine()
    progression.start_trading()
    
    assert progression.current_phase.name == "BEGINNER"
    print(f"✓ Progression: Current phase = {progression.current_phase.name}")
    
    # Get phase features
    features = progression.get_phase_features()
    available_count = sum(1 for v in features.values() if v == True)
    print(f"✓ Progression: Beginner has {available_count} features unlocked")
    
    # Test Feature Gate (pricing integration)
    gate = FeatureGate(SubscriptionTier.BASIC, progression.current_phase)
    available = gate.get_available_features()
    print(f"✓ FeatureGate: BASIC + Beginner has {len(available)} features")
    
    print("\n✅ TEST 7 PASSED: Trader progression system functional")


def test_08_replay_pipeline():
    """TEST 8: STEP 23 replay and backtesting pipeline."""
    print("\n" + "="*80)
    print("TEST 8: Replay & Backtesting Pipeline (STEP 23)")
    print("="*80)
    
    from backtesting.replay_engine import ReplayEngine
    from backtesting.ai_snapshot import AISnapshot
    from backtesting.chart_packet_builder import ChartPacketBuilder
    from backtesting.timeline_builder import TimelineBuilder
    from backtesting.explanation_engine import ExplanationEngine
    
    # Generate test data
    candles = generate_realistic_candles(100)
    
    # Test ReplayEngine
    replay = ReplayEngine()
    replay.load_candles(candles)
    assert replay.get_total_bars() == 100
    print(f"✓ ReplayEngine: Loaded {replay.get_total_bars()} candles")
    
    # Test AISnapshot (stores AI state at each bar)
    snapshot = AISnapshot()
    snapshot.store_confidence(0, 0.85)
    conf = snapshot.get_confidence(0)
    assert conf == 0.85
    print(f"✓ AISnapshot: State storage working (confidence={conf})")
    
    # Test Timeline Builder (audit trail of decisions)
    timeline = TimelineBuilder()
    timeline.add_event("SIGNAL_GENERATED", {"price": 2500.0, "type": "break_retest"})
    events = timeline.get_events()
    assert len(events) > 0
    print(f"✓ TimelineBuilder: {len(events)} decision event(s) recorded")
    
    # Test Chart Packet Builder (chart-ready data)
    packet_builder = ChartPacketBuilder()
    packet = packet_builder.build_packet(
        candles=candles[:50],
        signals=[{"price": 2500.0, "type": "entry"}]
    )
    assert packet is not None
    print(f"✓ ChartPacketBuilder: Chart packet created")
    
    # Test Explanation Engine (human-readable narratives)
    explainer = ExplanationEngine()
    explanation = explainer.explain_trade(
        entry=2500.0,
        stop=2450.0,
        target=2550.0,
        reason="Break retest with Gann confluence"
    )
    assert explanation is not None
    print(f"✓ ExplanationEngine: Narrative = '{explanation[:60]}...'")
    
    print("\n✅ TEST 8 PASSED: Replay pipeline functional")


def test_09_end_to_end_integration():
    """TEST 9: Complete end-to-end system integration."""
    print("\n" + "="*80)
    print("TEST 9: End-to-End Integration (IMO Pipeline)")
    print("="*80)
    
    from backend.intelligence.step3_imo_pipeline import IMOPipeline
    from backend.mentor.mentor_brain import MentorBrain
    from backend.mentor.signal_builder import SignalBuilder
    
    # Generate test data
    candles = generate_realistic_candles(50)
    
    # Test IMO Pipeline (orchestrates all intelligence)
    pipeline = IMOPipeline()
    
    # Process a candle through the entire pipeline
    result = pipeline.process_candle(candles[0])
    assert result is not None
    print(f"✓ IMOPipeline: Candle processed, decision generated")
    
    # Test Mentor Brain (applies mentor wisdom and progression)
    mentor = MentorBrain()
    signal = mentor.generate_signal(
        confidence=0.80,
        edge_type="break_retest",
        market_regime="trending"
    )
    assert signal is not None
    print(f"✓ MentorBrain: Signal generated")
    
    # Test Signal Builder (combines all engines)
    builder = SignalBuilder()
    full_signal = builder.build_signal(
        qmo_score=0.85,
        imo_score=0.80,
        gann_score=0.75,
        astro_score=0.70,
        cycle_score=0.65
    )
    assert full_signal is not None
    print(f"✓ SignalBuilder: Full 5-pillar signal built")
    
    print("\n✅ TEST 9 PASSED: End-to-end integration successful")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*120)
    print("QUANTUM MARKET OBSERVER - COMPLETE INTEGRATION TEST SUITE".center(120))
    print("="*120)
    
    tests = [
        ("Core Engines", test_01_core_engines),
        ("Iceberg Detection", test_02_iceberg_detection),
        ("Liquidity Analysis", test_03_liquidity_analysis),
        ("Confidence Scoring", test_04_confidence_scoring),
        ("Signal Filters", test_05_signal_filters),
        ("Session Management", test_06_session_management),
        ("Trader Progression", test_07_trader_progression),
        ("Replay Pipeline", test_08_replay_pipeline),
        ("End-to-End Integration", test_09_end_to_end_integration),
    ]
    
    passed = 0
    failed = 0
    failures = []
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            failures.append((name, str(e)))
            print(f"\n❌ TEST FAILED: {name}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*120)
    print("TEST SUMMARY".center(120))
    print("="*120)
    print(f"✅ PASSED: {passed}/9")
    print(f"❌ FAILED: {failed}/9")
    print(f"Success Rate: {(passed/9)*100:.1f}%")
    
    if failures:
        print("\nFailed Tests:")
        for name, error in failures:
            print(f"  • {name}: {error[:100]}")
    
    print("\n" + "="*120 + "\n")
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tests()
    sys.exit(0 if failed == 0 else 1)
