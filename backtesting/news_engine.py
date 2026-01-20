"""
STEP 23-B: News Engine
Injects news timestamps into replay
Prevents fake confidence during high-impact events
"""

from datetime import datetime, timedelta


class NewsEngine:
    """
    Tracks news events and creates awareness windows.
    High-impact news (CPI, NFP, FOMC) causes volatility spikes.
    """

    # Standard news impact categories
    IMPACT_HIGH = "HIGH"  # CPI, NFP, FOMC, major GDP
    IMPACT_MEDIUM = "MEDIUM"  # Inflation, interest rates, earnings
    IMPACT_LOW = "LOW"  # Housing, sentiment, minor data

    NEWS_TYPES = {
        "CPI": IMPACT_HIGH,
        "NFP": IMPACT_HIGH,
        "FOMC": IMPACT_HIGH,
        "GDP": IMPACT_HIGH,
        "INFLATION": IMPACT_MEDIUM,
        "INTEREST_RATE": IMPACT_MEDIUM,
        "EARNINGS": IMPACT_MEDIUM,
        "HOUSING": IMPACT_LOW,
        "SENTIMENT": IMPACT_LOW,
        "TRADE": IMPACT_MEDIUM,
    }

    def __init__(self, news_events=None):
        """
        Args:
            news_events: list of dicts
                {
                    "time": datetime,
                    "name": str,
                    "impact": "HIGH" | "MEDIUM" | "LOW"
                }
        """
        self.events = news_events or []

    def add_event(self, time, name, impact=None):
        """Add a news event"""
        if impact is None:
            impact = self.NEWS_TYPES.get(name, self.IMPACT_MEDIUM)

        self.events.append({
            "time": time if isinstance(time, datetime) else datetime.fromisoformat(time),
            "name": name,
            "impact": impact,
        })

    def check_news_window(self, candle_time, window_minutes=10):
        """
        Check if candle is within news event window.

        Args:
            candle_time: datetime object
            window_minutes: minutes before/after event to consider active

        Returns:
            {
                "active": bool,
                "impact": str | None,
                "name": str | None,
                "minutes_since": int (negative = before, positive = after)
            }
        """
        if isinstance(candle_time, str):
            candle_time = datetime.fromisoformat(candle_time)

        for event in self.events:
            delta_seconds = (candle_time - event["time"]).total_seconds()
            delta_minutes = delta_seconds / 60

            # Active window: from 5 min before to window_minutes after
            if -5 <= delta_minutes <= window_minutes:
                return {
                    "active": True,
                    "impact": event["impact"],
                    "name": event["name"],
                    "minutes_since": int(delta_minutes),
                }

        return {
            "active": False,
            "impact": None,
            "name": None,
            "minutes_since": None,
        }

    def get_news_before(self, candle_time, hours_before=24):
        """Get all news events in past N hours"""
        if isinstance(candle_time, str):
            candle_time = datetime.fromisoformat(candle_time)

        cutoff = candle_time - timedelta(hours=hours_before)
        return [e for e in self.events if cutoff <= e["time"] <= candle_time]

    def get_high_impact_days(self):
        """Return dates with HIGH impact news"""
        high_impact = [e for e in self.events if e["impact"] == self.IMPACT_HIGH]
        return list(set(e["time"].date() for e in high_impact))

    def is_quiet_period(self, candle_time, hours_before=1, hours_after=1):
        """
        Check if candle is in quiet period (no major news).
        Good for taking trades.
        """
        if isinstance(candle_time, str):
            candle_time = datetime.fromisoformat(candle_time)

        window_start = candle_time - timedelta(hours=hours_before)
        window_end = candle_time + timedelta(hours=hours_after)

        for event in self.events:
            if event["impact"] in [self.IMPACT_HIGH, self.IMPACT_MEDIUM]:
                if window_start <= event["time"] <= window_end:
                    return False

        return True

    def export_calendar(self):
        """Export news calendar for analysis"""
        return sorted(self.events, key=lambda e: e["time"])
