"""
STEP 23-B: Test — Session + News + Iceberg Awareness
Validates institutional-grade replay capabilities
"""

import sys
from datetime import datetime, timedelta

from backtesting import (
    SessionEngine,
    NewsEngine,
    IcebergMemory,
    ReplayFilters,
)


def test_session_engine():
    """Test session detection and kill zones"""
    print("\n" + "=" * 70)
    print("TEST 1: Session Engine")
    print("=" * 70)

    engine = SessionEngine()

    # Test times (UTC)
    test_cases = [
        ("2025-01-10T02:00:00", "ASIA"),
        ("2025-01-10T08:00:00", "LONDON"),
        ("2025-01-10T15:00:00", "NEW_YORK"),
        ("2025-01-10T22:00:00", "OFF_SESSION"),
    ]

    for time_str, expected_session in test_cases:
        time_obj = datetime.fromisoformat(time_str)
        session = engine.get_session(time_obj)
        status = "✓" if session == expected_session else "✗"
        print(f"{status} {time_str}: {session} (expected {expected_session})")

    # Test kill zones
    print("\nKill zone detection:")
    london_kill = datetime.fromisoformat("2025-01-10T08:30:00")
    is_kill = engine.is_killzone("LONDON", london_kill)
    print(f"  {'✓' if is_kill else '✗'} London 08:30 UTC: Kill zone = {is_kill}")

    ny_kill = datetime.fromisoformat("2025-01-10T14:45:00")
    is_kill = engine.is_killzone("NEW_YORK", ny_kill)
    print(f"  {'✓' if is_kill else '✗'} NewYork 14:45 UTC: Kill zone = {is_kill}")


def test_news_engine():
    """Test news event tracking"""
    print("\n" + "=" * 70)
    print("TEST 2: News Engine")
    print("=" * 70)

    engine = NewsEngine()

    # Add some news events
    engine.add_event(
        datetime.fromisoformat("2025-01-10T13:30:00"),
        "NFP",
        "HIGH"
    )
    engine.add_event(
        datetime.fromisoformat("2025-01-10T14:15:00"),
        "CPI",
        "HIGH"
    )

    # Test windows
    print("News event tracking:")
    
    # Before news
    before = datetime.fromisoformat("2025-01-10T13:20:00")
    news_info = engine.check_news_window(before)
    print(f"  {before}: News active = {news_info['active']}")

    # During news
    during = datetime.fromisoformat("2025-01-10T13:32:00")
    news_info = engine.check_news_window(during)
    status = "✓" if news_info["active"] else "✗"
    print(f"  {status} {during}: News active = {news_info['active']} ({news_info.get('name')})")

    # After news window
    after = datetime.fromisoformat("2025-01-10T13:50:00")
    news_info = engine.check_news_window(after)
    print(f"  {after}: News active = {news_info['active']}")

    # Quiet period check
    quiet_time = datetime.fromisoformat("2025-01-10T12:00:00")
    is_quiet = engine.is_quiet_period(quiet_time)
    print(f"\n  Quiet period check at {quiet_time}: {is_quiet}")


def test_iceberg_memory():
    """Test institutional volume persistence scoring"""
    print("\n" + "=" * 70)
    print("TEST 3: Iceberg Memory")
    print("=" * 70)

    memory = IcebergMemory()

    # Simulate institutional order at 2500.00
    print("Recording volume at 2500.00:")
    memory.record(2500.00, 500, "SELL", 0)
    memory.record_hit(2500.00)
    memory.record_hit(2500.00)
    memory.record_hit(2500.05)
    memory.record_hit(2499.98)

    score = memory.persistence_score(2500.00)
    ptype = memory.persistence_type(2500.00)
    print(f"  Persistence score: {score:.2f}")
    print(f"  Type: {ptype}")
    
    # Random volume
    memory.record(2505.00, 50, "BUY", 10)
    score_random = memory.persistence_score(2505.00)
    print(f"\n  Random volume score: {score_random:.2f}")
    print(f"  Type: {memory.persistence_type(2505.00)}")


def test_replay_filters():
    """Test signal quality gates"""
    print("\n" + "=" * 70)
    print("TEST 4: Replay Filters")
    print("=" * 70)

    filters = ReplayFilters()

    test_scenarios = [
        {
            "name": "Good London signal",
            "context": {
                "session": "LONDON",
                "killzone": False,
                "news": {"active": False},
                "iceberg_score": 0.8,
                "confidence": 0.85,
            },
            "expected": True,
        },
        {
            "name": "Signal during HIGH impact news",
            "context": {
                "session": "NEW_YORK",
                "killzone": False,
                "news": {"active": True, "impact": "HIGH", "name": "NFP"},
                "iceberg_score": 0.8,
                "confidence": 0.90,
            },
            "expected": False,
        },
        {
            "name": "Weak iceberg signal",
            "context": {
                "session": "LONDON",
                "killzone": False,
                "news": {"active": False},
                "iceberg_score": 0.2,  # Too low
                "confidence": 0.85,
            },
            "expected": False,
        },
        {
            "name": "Off-session signal",
            "context": {
                "session": "OFF_SESSION",
                "killzone": True,
                "news": {"active": False},
                "iceberg_score": 0.8,
                "confidence": 0.85,
            },
            "expected": False,
        },
    ]

    for scenario in test_scenarios:
        allowed = filters.allow_signal(scenario["context"])
        status = "✓" if allowed == scenario["expected"] else "✗"
        print(f"{status} {scenario['name']}: allowed={allowed}")


def test_integration():
    """Test all components together"""
    print("\n" + "=" * 70)
    print("TEST 5: Integration (Session + News + Iceberg + Filters)")
    print("=" * 70)

    session_engine = SessionEngine()
    news_engine = NewsEngine()
    iceberg = IcebergMemory()
    filters = ReplayFilters()

    # Simulate a replay scenario
    candle_time = datetime.fromisoformat("2025-01-10T14:30:00")

    # Add a news event
    news_engine.add_event(
        datetime.fromisoformat("2025-01-10T14:15:00"),
        "CPI",
        "HIGH"
    )

    # Record iceberg activity
    iceberg.record(2500.00, 500, "SELL", 100)
    iceberg.record_hit(2500.00)
    iceberg.record_hit(2500.05)

    # Build context (like replay engine would)
    context = {
        "session": session_engine.get_session(candle_time),
        "killzone": session_engine.is_killzone("NEW_YORK", candle_time),
        "news": news_engine.check_news_window(candle_time),
        "iceberg_score": iceberg.persistence_score(2500.00),
        "confidence": 0.80,
    }

    print(f"\nScenario: {candle_time}")
    print(f"  Session: {context['session']}")
    print(f"  Kill zone: {context['killzone']}")
    print(f"  News: {context['news']['active']} ({context['news'].get('name')})")
    print(f"  Iceberg score: {context['iceberg_score']:.2f}")
    print(f"  Confidence: {context['confidence']:.2f}")

    allowed = filters.allow_signal(context)
    print(f"\n  Signal allowed: {allowed}")
    print(f"  Reason: {'Passed all filters' if allowed else 'Blocked by filters'}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("STEP 23-B VALIDATION TESTS")
    print("Session + News + Iceberg-Aware Replay Engine")
    print("=" * 70)

    test_session_engine()
    test_news_engine()
    test_iceberg_memory()
    test_replay_filters()
    test_integration()

    print("\n" + "=" * 70)
    print("✅ ALL STEP 23-B TESTS COMPLETE")
    print("=" * 70)
    print("\nNext: 23-C for visual replay hooks and chart data formatting")
