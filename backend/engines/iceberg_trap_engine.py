class IcebergTrapEngine:
    def detect(self, zone, candles, retail_volume):
        impulse = candles[-1]["range"] > candles[-2]["range"] * 1.5
        opposite_break = (
            zone["side"] == "BUY" and candles[-1]["close"] < zone["low"]
        ) or (
            zone["side"] == "SELL" and candles[-1]["close"] > zone["high"]
        )

        if impulse and retail_volume > 0.7 and opposite_break:
            return True

        return False
