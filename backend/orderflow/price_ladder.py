from collections import defaultdict

class PriceLadder:
    def __init__(self, absorption_threshold=5000):
        self.ladder = defaultdict(lambda: {
            "buy_qty": 0,
            "sell_qty": 0,
            "total_qty": 0,
            "absorbed": False
        })
        self.absorption_threshold = absorption_threshold

    def update(self, price, side, quantity):
        if side == "BUY":
            self.ladder[price]["buy_qty"] += quantity
        else:
            self.ladder[price]["sell_qty"] += quantity
        self.ladder[price]["total_qty"] += quantity
        # Absorption logic
        if self.ladder[price]["total_qty"] > self.absorption_threshold:
            self.ladder[price]["absorbed"] = True

    def snapshot(self):
        return dict(self.ladder)
