class CycleEngine:
    cycles = [7, 14, 21, 30, 45, 90, 144, 180, 360]

    def is_cycle(self, bars):
        return bars in self.cycles
