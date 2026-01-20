class AngleEngine:
    """Analyzes angles and geometric relationships in price/time."""
    
    def calculate_angle(self, price_change, time_bars):
        """Calculate angle of price movement."""
        if time_bars == 0:
            return 0
        return (price_change / time_bars) * 45

    def is_harmonic_angle(self, angle):
        """Check if angle aligns with Gann harmonic angles."""
        harmonic_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        return any(abs(angle - ha) < 5 for ha in harmonic_angles)
