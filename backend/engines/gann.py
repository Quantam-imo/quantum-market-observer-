class GannEngine:
    def intraday_levels(self, high, low):
        r = abs(high - low)
        return {
            "100%": low + r,
            "150%": low + r * 1.5,
            "200%": low + r * 2
        }
