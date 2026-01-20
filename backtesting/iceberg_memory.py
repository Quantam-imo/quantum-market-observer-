"""
STEP 23-B: Iceberg Memory
Tracks institutional persistence of volume at price levels
Distinguishes institutional defense from random volume
"""


class IcebergMemory:
    """
    Records price levels where significant volume appeared.
    Institutions defend levels with repeated orders.
    This tracks persistence patterns.
    """

    def __init__(self):
        self.zones = []

    def record(self, price, volume, direction, candle_index):
        """
        Record a volume event at a price level.

        Args:
            price: float (price level)
            volume: int (volume at this level)
            direction: "BUY" | "SELL" | "BOTH"
            candle_index: int (which candle this occurred)
        """
        self.zones.append({
            "price": price,
            "volume": volume,
            "direction": direction,
            "first_seen": candle_index,
            "hit_count": 1,  # How many times price returned here
        })

    def record_hit(self, price, tolerance=2):
        """
        Record that price returned to a previously seen level.
        Indicates institutional interest / defense.
        """
        for zone in self.zones:
            if abs(zone["price"] - price) <= tolerance:
                zone["hit_count"] += 1
                break

    def persistence_score(self, price, tolerance=2):
        """
        Score how "persistent" is iceberg activity around this price.

        Scoring:
            0.0-0.3 → Random flow (no institutional interest)
            0.4-0.6 → Some interest (few revisits)
            0.7-0.9 → Institutional interest (5+ revisits)
            1.0 → Strong defense / absorption zone

        Args:
            price: current price
            tolerance: pip range to consider "same level"

        Returns:
            float 0.0-1.0
        """
        matching_zones = [
            z for z in self.zones
            if abs(z["price"] - price) <= tolerance
        ]

        if not matching_zones:
            return 0.0

        # Average hit count, normalized to 1.0
        avg_hits = sum(z["hit_count"] for z in matching_zones) / len(matching_zones)
        return min(avg_hits / 5.0, 1.0)  # Normalize (5+ hits = 1.0)

    def persistence_type(self, price, tolerance=2):
        """
        Classify the type of institutional activity.

        Returns:
            "RANDOM" | "INTEREST" | "DEFENSE" | "ABSORPTION"
        """
        score = self.persistence_score(price, tolerance)

        if score < 0.3:
            return "RANDOM"
        elif score < 0.6:
            return "INTEREST"
        elif score < 0.85:
            return "DEFENSE"
        else:
            return "ABSORPTION"

    def get_zones(self, price_range=5):
        """
        Get all active zones within price_range of current price.

        Returns:
            list of {price, volume, direction, hit_count, persistence_type}
        """
        zones = []
        for zone in self.zones:
            zone_data = {
                "price": zone["price"],
                "volume": zone["volume"],
                "direction": zone["direction"],
                "hit_count": zone["hit_count"],
                "persistence": self.persistence_type(zone["price"]),
            }
            zones.append(zone_data)

        return zones

    def cleanup_old_zones(self, max_zones=100):
        """
        Keep only most recent zones (institutions don't defend indefinitely).
        """
        if len(self.zones) > max_zones:
            self.zones = self.zones[-max_zones:]

    def export_zones(self):
        """Export all recorded zones for analysis"""
        return [
            {
                "price": z["price"],
                "volume": z["volume"],
                "direction": z["direction"],
                "first_seen_bar": z["first_seen"],
                "hit_count": z["hit_count"],
                "persistence": self.persistence_type(z["price"]),
            }
            for z in self.zones
        ]
