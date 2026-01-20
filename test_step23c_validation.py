#!/usr/bin/env python3
"""
test_step23c_validation.py
Comprehensive test suite for STEP 23-C (Explainable Replay)

Tests:
1. ExplanationEngine — Decision reasoning generation
2. TimelineBuilder — Audit trail recording
3. ChartPacketBuilder — Chart-ready data
4. Integration — All three working together in replay loop
"""

from datetime import datetime, timedelta
from backtesting.explanation_engine import ExplanationEngine
from backtesting.timeline_builder import TimelineBuilder
from backtesting.chart_packet_builder import ChartPacketBuilder


def test_explanation_engine():
    """Test AI decision explanations."""
    print("\n" + "=" * 80)
    print("TEST 1: ExplanationEngine")
    print("=" * 80)
    
    engine = ExplanationEngine()
    
    # Test 1a: Decision with confluence
    context_1 = {
        "session": "LONDON",
        "killzone": False,
        "news": {"active": True, "name": "CPI", "impact": "HIGH"},
        "iceberg_score": 0.82,
        "confidence": 0.85,
    }
    decision_1 = {
        "action": "BUY",
        "edge": "liquidity_confluence",
        "confidence": 0.85,
    }
    
    exp_1 = engine.build(context_1, decision_1)
    print(f"✓ Trade explanation: {exp_1['summary']}")
    assert exp_1["decision"] == "TRADE"
    assert "LONDON" in exp_1["summary"]
    assert "BUY" in exp_1["summary"]
    print(f"  Details: {len(exp_1['details'])} components")
    
    # Test 1b: Skip decision (killzone)
    context_2 = {
        "session": "NEW_YORK",
        "killzone": True,
        "news": {"active": False},
        "iceberg_score": 0.45,
        "confidence": 0.55,
    }
    
    exp_2 = engine.build(context_2, None)
    print(f"✓ Skip explanation: {exp_2['summary']}")
    assert exp_2["decision"] == "SKIP"
    assert "Killzone" in exp_2["summary"]
    
    # Test 1c: With mentor state (engine fusion)
    context_3 = {
        "session": "ASIA",
        "killzone": False,
        "news": {"active": False},
        "iceberg_score": 0.60,
        "confidence": 0.72,
    }
    mentor_state = {
        "qmo_signal": "BUY",
        "imo_signal": "HOLD",
        "gann_signal": "BUY",
        "astro_signal": "NEUTRAL",
        "cycle_signal": "BUY",
    }
    decision_3 = {"action": "SELL", "edge": "gann_reversal", "confidence": 0.78}
    
    exp_3 = engine.build(context_3, decision_3, mentor_state)
    print(f"✓ Fusion explanation: {exp_3['summary']}")
    assert "Consensus" in exp_3["summary"] or "QMO" in exp_3["summary"]
    
    print("\n✅ ExplanationEngine: All 3 tests passing")


def test_timeline_builder():
    """Test institutional audit trail."""
    print("\n" + "=" * 80)
    print("TEST 2: TimelineBuilder")
    print("=" * 80)
    
    timeline = TimelineBuilder()
    
    # Simulate 10 candles
    base_time = datetime(2025, 1, 10, 10, 0, 0)
    
    for i in range(10):
        candle = {
            "time": base_time + timedelta(minutes=5*i),
            "open": 3350 + i,
            "high": 3355 + i,
            "low": 3345 + i,
            "close": 3352 + i,
            "volume": 1000 + i*50,
        }
        
        context = {
            "session": "LONDON" if i < 5 else "NEW_YORK",
            "killzone": i == 3,
            "news": {"active": i == 7, "name": "NFP", "impact": "HIGH"},
            "iceberg_score": 0.5 + (i * 0.05),
            "confidence": 0.65 + (i * 0.02),
        }
        
        # Alternate trades and skips
        decision = None
        if i % 3 == 0:
            decision = {
                "action": "BUY" if i % 2 == 0 else "SELL",
                "edge": "cycle_confluence",
                "confidence": context["confidence"],
            }
        
        explanation = {
            "summary": f"Candle {i}: {'TRADE' if decision else 'SKIP'}",
            "details": [f"Session={context['session']}", f"Iceberg={context['iceberg_score']:.2f}"],
        }
        
        timeline.record(candle, context, decision, explanation)
    
    # Test 2a: Timeline length
    assert timeline.length() == 10
    print(f"✓ Timeline recorded 10 candles")
    
    # Test 2b: Trade/skip counts
    trades = timeline.get_trades_only()
    skips = timeline.get_skipped_only()
    print(f"✓ Trades: {len(trades)}, Skips: {len(skips)}")
    assert len(trades) + len(skips) == 10
    
    # Test 2c: Session filtering
    london_trades = timeline.get_session_trades("LONDON")
    print(f"✓ London trades: {len(london_trades)}")
    assert all(t["session"] == "LONDON" for t in london_trades)
    
    # Test 2d: Summary
    summary = timeline.get_summary()
    print(f"✓ Summary: {len(summary)} fields")
    assert summary["total_candles"] == 10
    assert summary["total_trades"] == len(trades)
    assert summary["skipped_trades"] == len(skips)
    
    # Test 2e: Export (test structure, not file I/O)
    exported = timeline.export()
    assert len(exported) == 10
    assert "time" in exported[0]
    assert "decision" in exported[0]
    assert "explanation" in exported[0]
    print(f"✓ Export structure correct ({len(exported)} entries)")
    
    print("\n✅ TimelineBuilder: All 5 tests passing")


def test_chart_packet_builder():
    """Test chart-ready data packets."""
    print("\n" + "=" * 80)
    print("TEST 3: ChartPacketBuilder")
    print("=" * 80)
    
    builder = ChartPacketBuilder()
    
    # Test 3a: Single packet
    candle = {
        "time": datetime(2025, 1, 10, 10, 0, 0),
        "open": 3350,
        "high": 3355,
        "low": 3345,
        "close": 3352,
        "volume": 1000,
    }
    context = {
        "session": "LONDON",
        "killzone": False,
        "news": {"active": False},
        "iceberg_score": 0.75,
        "confidence": 0.80,
    }
    decision = {"action": "BUY", "edge": "liquidity", "confidence": 0.80}
    explanation = {"summary": "Test"}
    
    packet = builder.build(candle, context, decision, explanation)
    print(f"✓ Packet keys: {len(packet)} fields")
    assert packet["signal"] == "BUY"
    assert packet["close"] == 3352
    assert packet["confidence"] == 0.80
    assert "time" in packet and "time" != ""
    
    # Test 3b: Recording packets
    builder.record(candle, context, decision, explanation)
    assert builder.length() == 1
    print(f"✓ Recorded 1 packet")
    
    # Test 3c: Signal filtering
    context_skip = context.copy()
    builder.record(candle, context_skip, None, explanation)
    
    signals = builder.get_signals()
    assert len(signals) == 1
    print(f"✓ Signals: {len(signals)}, Total: {builder.length()}")
    
    # Test 3d: Session filtering
    context_ny = context.copy()
    context_ny["session"] = "NEW_YORK"
    builder.record(candle, context_ny, decision, explanation)
    
    ny_packets = builder.get_by_session("NEW_YORK")
    assert len(ny_packets) == 1
    print(f"✓ Session filter: {len(ny_packets)} NY packets")
    
    # Test 3e: Confidence filtering
    high_conf = builder.get_high_confidence(0.75)
    print(f"✓ High confidence (≥0.75): {len(high_conf)} packets")
    assert all(p["confidence"] >= 0.75 or p["confidence"] == 0.0 for p in high_conf)
    
    # Test 3f: Killzone packets
    context_kill = context.copy()
    context_kill["killzone"] = True
    builder.record(candle, context_kill, decision, explanation)
    
    kill_packets = builder.get_killzone_packets()
    print(f"✓ Killzone packets: {len(kill_packets)}")
    assert all(p["killzone"] for p in kill_packets)
    
    # Test 3g: Export structure
    exported = builder.export()
    assert len(exported) > 0
    assert all("time" in p and "signal" in p for p in exported)
    print(f"✓ Export: {len(exported)} packets")
    
    print("\n✅ ChartPacketBuilder: All 7 tests passing")


def test_integration_full_flow():
    """Test all three components working together."""
    print("\n" + "=" * 80)
    print("TEST 4: Full Integration")
    print("=" * 80)
    
    explainer = ExplanationEngine()
    timeline = TimelineBuilder()
    chart = ChartPacketBuilder()
    
    # Simulate 5-candle flow
    base_time = datetime(2025, 1, 10, 10, 0, 0)
    
    for i in range(5):
        candle = {
            "time": base_time + timedelta(minutes=5*i),
            "open": 3350 + i,
            "high": 3355 + i,
            "low": 3345 + i,
            "close": 3352 + i,
            "volume": 1000 + i*50,
        }
        
        context = {
            "session": "LONDON",
            "killzone": False,
            "news": {"active": False},
            "iceberg_score": 0.60 + (i * 0.05),
            "confidence": 0.70 + (i * 0.03),
        }
        
        # Trade on i=2
        decision = None
        if i == 2:
            decision = {"action": "BUY", "edge": "confluence", "confidence": 0.76}
        
        # Step 1: Explanation
        explanation = explainer.build(context, decision)
        
        # Step 2: Timeline
        timeline.record(candle, context, decision, explanation)
        
        # Step 3: Chart packet
        chart.record(candle, context, decision, explanation)
    
    # Verify full flow
    assert timeline.length() == 5
    assert chart.length() == 5
    print(f"✓ Full flow: 5 candles recorded")
    
    timeline_trades = len(timeline.get_trades_only())
    chart_signals = len(chart.get_signals())
    assert timeline_trades == chart_signals == 1
    print(f"✓ Trades sync: Timeline={timeline_trades}, Chart={chart_signals}")
    
    summary = timeline.get_summary()
    assert summary["total_trades"] == 1
    print(f"✓ Summary: {summary['total_trades']} trade, {summary['skipped_trades']} skips")
    
    # Verify explanations present in timeline
    for entry in timeline.export():
        assert entry["explanation"] is not None
        exp = entry["explanation"]
        assert isinstance(exp, dict) or (isinstance(exp, str) and len(exp) > 0)
    print(f"✓ All timeline entries have explanations")
    
    # Verify packets have tooltips
    for packet in chart.export():
        if packet["signal"]:  # Only trade packets
            assert packet["tooltip"] is not None
            print(f"  - {packet['signal']} at {packet['time']}: {packet['tooltip'][:50]}...")
    
    print("\n✅ Integration: All 5 tests passing")


def test_edge_cases():
    """Test edge cases and boundaries."""
    print("\n" + "=" * 80)
    print("TEST 5: Edge Cases")
    print("=" * 80)
    
    explainer = ExplanationEngine()
    timeline = TimelineBuilder()
    chart = ChartPacketBuilder()
    
    # Edge case 1: Zero confidence
    context_zero = {
        "session": "ASIA",
        "killzone": True,
        "news": {"active": True, "name": "TEST", "impact": "HIGH"},
        "iceberg_score": 0.0,
        "confidence": 0.0,
    }
    exp = explainer.build(context_zero, None)
    assert exp["confidence"] == 0.0
    print(f"✓ Zero confidence handled: {exp['summary'][:50]}...")
    
    # Edge case 2: High iceberg + high confidence
    context_high = {
        "session": "NEW_YORK",
        "killzone": False,
        "news": {"active": False},
        "iceberg_score": 1.0,
        "confidence": 0.99,
    }
    decision_high = {"action": "SELL", "edge": "absorption", "confidence": 0.99}
    exp = explainer.build(context_high, decision_high)
    assert exp["confidence"] == 0.99
    print(f"✓ High values handled: {exp['summary'][:50]}...")
    
    # Edge case 3: Empty timeline/chart
    assert timeline.length() == 0
    assert chart.length() == 0
    print(f"✓ Empty structures: timeline={timeline.length()}, chart={chart.length()}")
    
    # Edge case 4: Unknown session
    context_unknown = {
        "session": "UNKNOWN",
        "killzone": False,
        "news": {"active": False},
        "iceberg_score": 0.5,
        "confidence": 0.7,
    }
    exp = explainer.build(context_unknown, None)
    assert "UNKNOWN" in exp["summary"]
    print(f"✓ Unknown session handled")
    
    # Edge case 5: Missing news data
    context_no_news = {
        "session": "LONDON",
        "killzone": False,
        # news missing
        "iceberg_score": 0.5,
        "confidence": 0.7,
    }
    exp = explainer.build(context_no_news, None)
    assert exp is not None
    print(f"✓ Missing news data handled")
    
    print("\n✅ Edge Cases: All 5 tests passing")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("STEP 23-C VALIDATION: EXPLAINABLE REPLAY + CHART-READY DATA")
    print("=" * 80)
    
    test_explanation_engine()
    test_timeline_builder()
    test_chart_packet_builder()
    test_integration_full_flow()
    test_edge_cases()
    
    print("\n" + "=" * 80)
    print("✅ ALL STEP 23-C TESTS PASSING (5/5 TEST GROUPS)")
    print("=" * 80)
    print("""
    Summary:
    ✓ ExplanationEngine: Decisions explained (trade/skip reasoning)
    ✓ TimelineBuilder: Audit trail recorded (institutional grade)
    ✓ ChartPacketBuilder: Chart packets ready (UI-ready data)
    ✓ Integration: All components working together
    ✓ Edge Cases: Boundary conditions handled
    
    You now have:
    1. AI thought process per candle (explainability)
    2. Full replay history (audit trail)
    3. Chart-ready packets (UI preparation)
    
    NEXT: Reply with '23-D' to build visual replay hooks
    """)


if __name__ == "__main__":
    main()
