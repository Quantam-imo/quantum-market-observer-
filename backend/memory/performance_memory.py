class PerformanceMemory:
    def __init__(self):
        self.trades = []

    def log_trade(self, trade_data):
        self.trades.append(trade_data)

    def recent(self, n=50):
        return self.trades[-n:]
