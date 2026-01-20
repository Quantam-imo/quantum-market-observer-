class LiquidityEngine:
    """Analyzes institutional liquidity zones and order flow."""
    
    def detect_liquidity_pool(self, support, resistance, volume):
        """Identify liquidity concentration areas."""
        if volume > 1000:
            return {"level": (support + resistance) / 2, "strength": volume / 100}
        return None

    def sweep_probability(self, low, high, bid_volume):
        """Calculate probability of liquidity sweep."""
        return bid_volume > high * 2
