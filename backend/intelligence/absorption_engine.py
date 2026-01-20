"""
Absorption Engine — Detects institutional absorption zones
Identifies where large volume clusters with minimal price movement occur
This is where institutions defend or build positions
"""

class AbsorptionEngine:
    """
    Detects absorption zones from trade data.
    Absorption = High volume at stable price = Institutional activity
    """
    
    def __init__(self, threshold=400):
        self.threshold = threshold
        self.absorption_history = []
    
    def detect(self, trades):
        """
        Cluster trades by price level and detect absorption zones.
        
        Args:
            trades: List of trade dictionaries {price, size, side, timestamp}
        
        Returns:
            List of absorption zones with metadata
        """
        if not trades:
            return []
        
        volume_by_price = {}
        price_range_info = {}
        
        # Cluster trades by price (rounded to 0.1 precision)
        for t in trades:
            price = round(t["price"], 1)
            size = t.get("size", 1)
            side = t.get("side", "UNKNOWN")
            
            if price not in volume_by_price:
                volume_by_price[price] = {"total": 0, "buy": 0, "sell": 0}
                price_range_info[price] = []
            
            volume_by_price[price]["total"] += size
            if side == "BUY":
                volume_by_price[price]["buy"] += size
            elif side == "SELL":
                volume_by_price[price]["sell"] += size
            
            price_range_info[price].append(t)
        
        # Identify absorption zones
        zones = []
        for price, volume_data in volume_by_price.items():
            if volume_data["total"] >= self.threshold:
                # Determine dominance
                buy_ratio = volume_data["buy"] / volume_data["total"] if volume_data["total"] > 0 else 0.5
                dominance = "BUY" if buy_ratio > 0.6 else "SELL" if buy_ratio < 0.4 else "NEUTRAL"
                
                zone = {
                    "price": price,
                    "volume": volume_data["total"],
                    "type": "ABSORPTION",
                    "dominance": dominance,
                    "buy_volume": volume_data["buy"],
                    "sell_volume": volume_data["sell"],
                    "trade_count": len(price_range_info[price]),
                    "strength": min(volume_data["total"] / self.threshold, 3.0)  # 1.0 = threshold, 3.0+ = very strong
                }
                zones.append(zone)
                self.absorption_history.append(zone)
        
        return sorted(zones, key=lambda x: x["volume"], reverse=True)
    
    def get_active_absorptions(self, current_price, tolerance=5):
        """
        Get absorption zones near current price within tolerance.
        
        Args:
            current_price: Current market price
            tolerance: Price tolerance in points
        
        Returns:
            List of nearby absorption zones
        """
        active = []
        for zone in self.absorption_history[-100:]:  # Only check recent
            if abs(zone["price"] - current_price) <= tolerance:
                active.append(zone)
        return active
