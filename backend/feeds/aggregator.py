from collections import deque

class TickAggregator:
    def __init__(self, window=50):
        self.ticks = deque(maxlen=window)

    def add(self, tick):
        self.ticks.append(tick)

    def snapshot(self):
        buys = sum(t["qty"] for t in self.ticks if t["side"] == "buy")
        sells = sum(t["qty"] for t in self.ticks if t["side"] == "sell")
        price = self.ticks[-1]["price"] if self.ticks else None
        return price, buys, sells
