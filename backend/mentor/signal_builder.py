class SignalBuilder:
    """Constructs trade signals from multiple data sources."""
    
    def build_signal(self, qmo, imo, gann, astro, cycle):
        """Combine all engines into actionable signal."""
        return {
            "qmo": qmo,
            "imo": imo,
            "gann": gann,
            "astro": astro,
            "cycle": cycle,
            "timestamp": None
        }

    def generate_recommendation(self, signal, confidence):
        """Generate final trading recommendation."""
        if confidence > 0.75:
            return "STRONG BUY" if signal["qmo"] else "STRONG SELL"
        elif confidence > 0.6:
            return "BUY" if signal["qmo"] else "SELL"
        return "NEUTRAL"
