class OrderFlowEngine:
    def analyze(self, buys, sells):
        delta = buys - sells
        return {
            "buys": buys,
            "sells": sells,
            "delta": delta
        }
