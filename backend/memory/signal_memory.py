class SignalMemory:
    """Tracks generated signals and their performance."""
    
    def __init__(self):
        self.signals = []

    def store_signal(self, signal, entry, exit=None, pnl=None):
        """Save signal with outcome data."""
        self.signals.append({
            "signal": signal,
            "entry": entry,
            "exit": exit,
            "pnl": pnl
        })

    def win_rate(self):
        """Calculate signal success rate."""
        if not self.signals:
            return 0
        wins = sum(1 for s in self.signals if s["pnl"] and s["pnl"] > 0)
        return wins / len(self.signals)
