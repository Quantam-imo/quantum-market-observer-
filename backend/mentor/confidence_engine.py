class ConfidenceEngine:
    weights = {"QMO":0.3,"IMO":0.25,"GANN":0.2,"ASTRO":0.15,"CYCLE":0.1}

    def score(self, s):
        return sum(s[k]*self.weights[k] for k in s)
