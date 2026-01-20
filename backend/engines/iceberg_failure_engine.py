class IcebergFailureEngine:
    def evaluate(self, zone, candles):
        last = candles[-1]

        # Clean break
        if zone["side"] == "BUY" and last["close"] < zone["low"]:
            return "FAILED"

        if zone["side"] == "SELL" and last["close"] > zone["high"]:
            return "FAILED"

        # Wick rejection absence
        if last.get("wick_strength", 1.0) < 0.2:
            return "WEAK"

        return "VALID"
