class PriceDegreEngine:
    """Converts price movements to degrees for harmonic analysis."""
    
    def price_to_degree(self, price, base_price, scale=100):
        """Convert price difference to degrees."""
        return ((price - base_price) / scale) * 360

    def get_harmonic_degrees(self, price, base_price):
        """Get harmonic angles for a price level."""
        degree = self.price_to_degree(price, base_price)
        return degree % 360
