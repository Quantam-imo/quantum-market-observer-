class MentorBrain:
    def decide(self, ctx):
        if not ctx["qmo"] or not ctx["imo"]:
            return None
        if ctx["confidence"] < 0.7:
            return None
        return ctx
