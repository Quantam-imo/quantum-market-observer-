class QMOAdapter:
    def allowed(self, phase):
        return phase in ["ACCUMULATION", "DISTRIBUTION", "EXPANSION"]
