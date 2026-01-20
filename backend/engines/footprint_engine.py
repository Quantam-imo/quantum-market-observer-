class FootprintEngine:
    def __init__(self):
        self.candles = {}

    def update(self, candle_id, buy_qty, sell_qty):
        self.candles[candle_id] = {
            "buy": buy_qty,
            "sell": sell_qty,
            "delta": buy_qty - sell_qty
        }

    def get(self, candle_id):
        return self.candles.get(candle_id, {})
