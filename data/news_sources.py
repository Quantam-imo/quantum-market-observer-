class NewsSources:
    """Manages economic news feeds and event calendars."""
    
    HIGH_IMPACT = ["CPI", "NFP", "FOMC Rate Decision", "GDP", "Unemployment Rate"]
    MEDIUM_IMPACT = ["Retail Sales", "Consumer Sentiment", "Housing Starts"]
    LOW_IMPACT = ["Building Permits", "Industrial Production"]

    @classmethod
    def is_high_impact(cls, event):
        return event in cls.HIGH_IMPACT

    @classmethod
    def filter_by_date(cls, events, date):
        """Get news events for a specific date."""
        return [e for e in events if e.get("date") == date]
