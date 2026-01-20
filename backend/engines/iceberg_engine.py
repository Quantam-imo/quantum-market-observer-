class IcebergEngine:
    def __init__(self, delta_threshold=1500, price_tolerance=0.3):
        self.delta_threshold = delta_threshold
        self.price_tolerance = price_tolerance
        self.icebergs = []

    def check_absorption(self, price, delta, price_move):
        if abs(delta) >= self.delta_threshold and abs(price_move) <= self.price_tolerance:
            iceberg = {
                "price": price,
                "delta": delta,
                "type": "SELL" if delta < 0 else "BUY"
            }
            self.icebergs.append(iceberg)
            return iceberg
        return None

    def recent(self, n=5):
        return self.icebergs[-n:]

    @staticmethod
    def detect_iceberg(candles, direction, average_volume, small_range, wick_threshold):
        recent = candles[-5:]
        volume_spike = sum(c["volume"] for c in recent) > 1.8 * average_volume
        price_stall = abs(recent[-1]["close"] - recent[0]["open"]) < small_range
        wick_pressure = any(
            c["high"] - c["close"] > wick_threshold for c in recent
        )

        if direction == "SELL":
            return volume_spike and price_stall and wick_pressure
        if direction == "BUY":
            return volume_spike and price_stall
