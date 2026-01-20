class GannTargetEngine:
    def __init__(self):
        self.multipliers = [0.5, 1, 1.5, 2, 2.5, 4]

    def project(self, base_range, entry, direction):
        targets = []
        for m in self.multipliers:
            if direction == "BUY":
                targets.append(round(entry + base_range * m, 2))
            else:
                targets.append(round(entry - base_range * m, 2))
        return targets
