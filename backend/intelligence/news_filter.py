class NewsFilter:
    def risk(self, event):
        return event in ["CPI", "NFP", "FOMC"]
