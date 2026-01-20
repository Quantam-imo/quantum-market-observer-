"""
STEP 23-B: Session Engine
Identifies trading session and kill zones
Asia / London / NewYork with high-risk periods
"""

from datetime import datetime, time


class SessionEngine:
    """
    Determines current trading session based on UTC time.
    Also identifies kill zones (high-spread, unpredictable periods).
    """

    def __init__(self, timezone_utc=True):
        """
        Args:
            timezone_utc: If True, times are UTC. If False, convert from user timezone.
        """
        self.timezone_utc = timezone_utc

    def get_session(self, candle_time):
        """
        Determine session from candle timestamp.

        Args:
            candle_time: datetime object

        Returns:
            "ASIA" | "LONDON" | "NEW_YORK" | "OFF_SESSION"
        """
        if isinstance(candle_time, str):
            # Parse ISO format
            candle_time = datetime.fromisoformat(candle_time)

        t = candle_time.time()

        # ---- SESSION DEFINITIONS (UTC) ----
        # Asia: 00:00-06:00 UTC (low volume, choppy)
        if time(0, 0) <= t < time(6, 0):
            return "ASIA"

        # London: 06:00-13:00 UTC (high volume, trending)
        if time(6, 0) <= t < time(13, 0):
            return "LONDON"

        # NewYork: 13:00-21:00 UTC (highest volume, volatile)
        if time(13, 0) <= t < time(21, 0):
            return "NEW_YORK"

        # Off-session: 21:00-00:00 UTC (low, unpredictable)
        return "OFF_SESSION"

    def is_killzone(self, session, candle_time):
        """
        High-risk periods with wide spreads and low predictability.

        Args:
            session: session string
            candle_time: datetime object

        Returns:
            bool - True if in kill zone
        """
        if isinstance(candle_time, str):
            candle_time = datetime.fromisoformat(candle_time)

        t = candle_time.time()

        # London kill zone: 07:00-10:00 (opens often spike, then chop)
        if session == "LONDON" and time(7, 0) <= t <= time(10, 0):
            return True

        # NewYork kill zone: 13:30-16:00 (FOMC, NFP, data releases clustered)
        if session == "NEW_YORK" and time(13, 30) <= t <= time(16, 0):
            return True

        # Off-session (all): always kill zone
        if session == "OFF_SESSION":
            return True

        return False

    def session_quality(self, session):
        """
        Return expected volatility and reliability for each session.

        Returns:
            {
                "volatility": "LOW" | "MEDIUM" | "HIGH",
                "reliability": 0.0-1.0,
                "volume": "LOW" | "NORMAL" | "HIGH"
            }
        """
        qualities = {
            "ASIA": {
                "volatility": "LOW",
                "reliability": 0.65,
                "volume": "LOW",
            },
            "LONDON": {
                "volatility": "MEDIUM",
                "reliability": 0.85,
                "volume": "HIGH",
            },
            "NEW_YORK": {
                "volatility": "HIGH",
                "reliability": 0.80,
                "volume": "HIGH",
            },
            "OFF_SESSION": {
                "volatility": "HIGH",
                "reliability": 0.30,
                "volume": "LOW",
            },
        }
        return qualities.get(session, {})

    def get_all_sessions(self):
        """Return all session names"""
        return ["ASIA", "LONDON", "NEW_YORK", "OFF_SESSION"]
