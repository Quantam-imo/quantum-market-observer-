class AstroEngine:
    major_aspects = [0, 60, 90, 120, 180]

    def aspect(self, d1, d2):
        diff = abs(d1 - d2) % 360
        return min(diff, 360 - diff)

    def is_major(self, d1, d2):
        return any(abs(self.aspect(d1, d2) - a) <= 1 for a in self.major_aspects)
