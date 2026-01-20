"""
STEP 23-B: Replay Filters
Signal quality gates
Prevents trading in low-quality conditions
"""


class ReplayFilters:
    """
    Institutional-grade signal filters.
    Not all signals are equal. Filter out low-quality ones.
    """

    def __init__(self):
        """Initialize filter configuration"""
        self.min_confidence = 0.70
        self.min_iceberg_score = 0.5
        self.allow_killzone = False
        self.allow_high_impact_news = False
        self.allow_off_session = False

    def allow_signal(self, context):
        """
        Comprehensive signal quality check.

        Args:
            context: dict with keys:
                - session: "ASIA" | "LONDON" | "NEW_YORK" | "OFF_SESSION"
                - killzone: bool
                - news: {active, impact, name, minutes_since}
                - iceberg_score: float 0.0-1.0
                - confidence: float 0.0-1.0

        Returns:
            bool - True if signal passes all filters
        """
        # ---- FILTER 1: SESSION RESTRICTION ----
        if context.get("session") == "OFF_SESSION" and not self.allow_off_session:
            return False

        # ---- FILTER 2: KILL ZONE AVOIDANCE ----
        if context.get("killzone", False) and not self.allow_killzone:
            return False

        # ---- FILTER 3: NEWS AWARENESS ----
        news = context.get("news", {})
        if news.get("active"):
            # High-impact news: block entirely
            if news.get("impact") == "HIGH" and not self.allow_high_impact_news:
                return False

            # Medium-impact: require higher confidence
            if news.get("impact") == "MEDIUM":
                if context.get("confidence", 0) < 0.80:
                    return False

        # ---- FILTER 4: ICEBERG PERSISTENCE ----
        iceberg_score = context.get("iceberg_score", 0.0)
        if iceberg_score < self.min_iceberg_score:
            return False

        # ---- FILTER 5: CONFIDENCE MINIMUM ----
        if context.get("confidence", 0) < self.min_confidence:
            return False

        # ---- ALL FILTERS PASSED ----
        return True

    def allow_signal_lenient(self, context):
        """
        Lenient filters (for low-volume sessions like Asia).
        Same as allow_signal but lower thresholds.
        """
        # Temporarily adjust thresholds
        old_min_conf = self.min_confidence
        old_min_iceberg = self.min_iceberg_score

        self.min_confidence = 0.65
        self.min_iceberg_score = 0.3

        result = self.allow_signal(context)

        # Restore
        self.min_confidence = old_min_conf
        self.min_iceberg_score = old_min_iceberg

        return result

    def allow_signal_strict(self, context):
        """
        Strict filters (for high-volume, high-volatility sessions).
        Block most signals, only take best ones.
        """
        # Temporarily adjust thresholds
        old_min_conf = self.min_confidence
        old_min_iceberg = self.min_iceberg_score

        self.min_confidence = 0.85
        self.min_iceberg_score = 0.7

        result = self.allow_signal(context)

        # Restore
        self.min_confidence = old_min_conf
        self.min_iceberg_score = old_min_iceberg

        return result

    def filter_by_session(self, context):
        """
        Get appropriate filter set based on session volatility.

        Returns:
            "STRICT" | "NORMAL" | "LENIENT"
        """
        session = context.get("session")

        if session == "LONDON":
            return "NORMAL"
        elif session == "NEW_YORK":
            return "STRICT"
        elif session == "ASIA":
            return "LENIENT"
        else:
            return "STRICT"

    def get_filter_summary(self):
        """Return current filter configuration"""
        return {
            "min_confidence": self.min_confidence,
            "min_iceberg_score": self.min_iceberg_score,
            "allow_killzone": self.allow_killzone,
            "allow_high_impact_news": self.allow_high_impact_news,
            "allow_off_session": self.allow_off_session,
        }

    def set_session_filters(self, session):
        """
        Auto-configure filters based on session.
        """
        if session == "LONDON":
            self.min_confidence = 0.70
            self.min_iceberg_score = 0.5
            self.allow_killzone = False

        elif session == "NEW_YORK":
            self.min_confidence = 0.80
            self.min_iceberg_score = 0.7
            self.allow_killzone = False

        elif session == "ASIA":
            self.min_confidence = 0.65
            self.min_iceberg_score = 0.3
            self.allow_killzone = True  # More lenient

        else:  # OFF_SESSION
            self.allow_off_session = False
