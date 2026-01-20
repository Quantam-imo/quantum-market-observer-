class FailureEngine:
    def classify(self, price_stall, time_invalid, structure_break):
        if structure_break or time_invalid:
            return "HARD_FAILURE"
        if price_stall:
            return "SOFT_FAILURE"
        return "NO_FAILURE"
