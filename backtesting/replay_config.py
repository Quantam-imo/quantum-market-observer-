"""
STEP 23: Replay Configuration
Asset / date / session configuration for historical tests
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta


@dataclass
class ReplayConfig:
    """Configuration for a single replay test"""

    asset: str  # "GC" (COMEX Gold), "XAUUSD", etc
    timeframe: int = 1  # minutes (1, 5, 15, 60)
    start_date: str = None  # "2025-01-01"
    end_date: str = None  # "2025-01-07"
    sessions: List[str] = None  # ["LONDON", "NEWYORK"]
    
    def __post_init__(self):
        if not self.sessions:
            self.sessions = ["LONDON", "NEWYORK"]

    def to_dict(self):
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "sessions": self.sessions,
        }


# Pre-defined test scenarios
TEST_SCENARIOS = {
    "first_week_gc": ReplayConfig(
        asset="GC",
        timeframe=1,
        start_date="2025-01-06",  # Monday
        end_date="2025-01-10",  # Friday
        sessions=["LONDON", "NEWYORK"],
    ),
    "volatile_week": ReplayConfig(
        asset="GC",
        timeframe=1,
        start_date="2025-01-13",  # High volatility week
        end_date="2025-01-17",
        sessions=["ASIA", "LONDON", "NEWYORK"],
    ),
    "single_day": ReplayConfig(
        asset="GC",
        timeframe=1,
        start_date="2025-01-10",
        end_date="2025-01-10",
        sessions=["LONDON", "NEWYORK"],
    ),
}


def get_test_scenario(name: str) -> ReplayConfig:
    """Get pre-defined test scenario"""
    return TEST_SCENARIOS.get(name)


def list_scenarios() -> List[str]:
    """List all available test scenarios"""
    return list(TEST_SCENARIOS.keys())
