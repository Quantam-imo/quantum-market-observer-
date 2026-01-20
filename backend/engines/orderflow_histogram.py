class OrderFlowHistogram:
    def __init__(self):
        self.bars = {}

    def update(self, candle_time, buy_qty, sell_qty):
        self.bars[candle_time] = {
            "buy": buy_qty,
            "sell": sell_qty,
            "delta": buy_qty - sell_qty
        }

    def get_bar(self, candle_time):
        return self.bars.get(candle_time, {
            "buy": 0,
            "sell": 0,
            "delta": 0
        })

    def last_n(self, n=50):
        return list(self.bars.items())[-n:]
