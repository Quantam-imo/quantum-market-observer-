import websocket
import json
from collections import defaultdict

class CMEDeltaFeed:
    def __init__(self):
        self.price_map = defaultdict(lambda: {"buy": 0, "sell": 0})

    def on_message(self, ws, message):
        data = json.loads(message)
        price = float(data["price"])
        qty = int(data["quantity"])
        side = data["side"]  # "BUY" or "SELL"
        if side == "BUY":
            self.price_map[price]["buy"] += qty
        else:
            self.price_map[price]["sell"] += qty

    def get_delta(self, price):
        p = self.price_map[price]
        return p["buy"] - p["sell"]

    def reset(self):
        self.price_map.clear()
