class GannEngine:
    multipliers = [0.5, 1, 1.5, 2, 2.5, 4, 6, 8]

    def levels(self, high, low):
        base = abs(high - low)
        return {f"{int(m*100)}%": round(base * m, 2) for m in self.multipliers}
