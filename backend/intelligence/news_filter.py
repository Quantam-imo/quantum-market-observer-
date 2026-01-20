
class NewsFilter:
    def risk(self, event):
        return event in ["CPI", "NFP", "FOMC"]

    @staticmethod
    def news_trade_allowed(news_type, minutes_to_news):
        if minutes_to_news <= 3:
            return False  # spread chaos
        if news_type == "SHOCK":
            return False
        return True
