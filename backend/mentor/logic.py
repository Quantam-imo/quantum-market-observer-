from config import CONFIDENCE_THRESHOLD

class MentorLogic:
    def evaluate(self, ctx):
        score = 0

        if ctx["iceberg"]:
            score += 0.4
        if ctx["astro"]:
            score += 0.2
        if ctx["cycle"]:
            score += 0.2
        if ctx["delta"] < 0:
            score += 0.2

        if score >= CONFIDENCE_THRESHOLD:
            return {
                "decision": "SELL" if ctx["delta"] < 0 else "BUY",
                "confidence": round(score * 100, 1)
            }
        return {"decision": "WAIT", "confidence": round(score * 100, 1)}
