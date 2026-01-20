# backtesting/explanation_engine.py
"""
ExplanationEngine: Generates human-readable reasoning for every candle decision.

This is the differentiator between "black box" and "institutional-grade" systems.
Every trade (and skip) is explained to auditors/partners.
"""


class ExplanationEngine:
    """Converts AI internal state → human-readable decision narrative."""
    
    def __init__(self):
        """Initialize explanation engine with zero state."""
        self.last_explanation = None
    
    def build(self, context, decision, mentor_state=None):
        """
        Build complete explanation for why AI did/didn't trade.
        
        Args:
            context: Dict with session, killzone, news, iceberg_score, confidence, etc.
            decision: Dict with action, confidence, edge, or None
            mentor_state: Optional dict with engine states (qmo, imo, gann, astro, cycle)
        
        Returns:
            Dict with summary string + detailed breakdown
        """
        reasons = []
        
        # FOUNDATION: Session awareness
        session = context.get("session", "UNKNOWN")
        reasons.append(f"Session: {session}")
        
        # RISK: Kill zone blocking
        if context.get("killzone", False):
            reasons.append("⚠️ Killzone active (high volatility period)")
        
        # NEWS: Event proximity
        news = context.get("news", {})
        if news and news.get("active", False):
            impact = news.get("impact", "UNKNOWN")
            event_name = news.get("name", "Event")
            minutes = news.get("minutes_since", "?")
            reasons.append(
                f"📰 News: {event_name} ({impact}) — {minutes}min window"
            )
        
        # INSTITUTIONAL: Volume persistence
        iceberg_score = context.get("iceberg_score", 0.0)
        reasons.append(f"🧊 Iceberg persistence: {iceberg_score:.2f}/1.0")
        
        # ENGINE FUSION (if provided)
        if mentor_state:
            qmo_signal = mentor_state.get("qmo_signal")
            imo_signal = mentor_state.get("imo_signal")
            gann_signal = mentor_state.get("gann_signal")
            astro_signal = mentor_state.get("astro_signal")
            cycle_signal = mentor_state.get("cycle_signal")
            
            signals = [
                ("QMO", qmo_signal),
                ("IMO", imo_signal),
                ("Gann", gann_signal),
                ("Astro", astro_signal),
                ("Cycle", cycle_signal),
            ]
            active_engines = [name for name, sig in signals if sig]
            
            if active_engines:
                reasons.append(f"🔀 Consensus: {' + '.join(active_engines)}")
        
        # CONFIDENCE: Quality gate
        confidence = context.get("confidence", 0.0)
        confidence_pct = int(confidence * 100)
        reasons.append(f"🎯 Confidence: {confidence_pct}%")
        
        # DECISION: Final outcome
        if decision:
            action = decision.get("action", "UNKNOWN").upper()
            edge = decision.get("edge", "unknown")
            reason = f"✅ {action} — Edge: {edge}"
            reasons.append(reason)
            summary_text = " | ".join(reasons)
        else:
            reasons.append("⏭️ Skip — Conditions incomplete")
            summary_text = " | ".join(reasons)
        
        self.last_explanation = {
            "summary": summary_text,
            "details": reasons,
            "decision": "TRADE" if decision else "SKIP",
            "confidence": confidence,
            "session": session,
        }
        
        return self.last_explanation
    
    def get_last_explanation(self):
        """Retrieve previous explanation (for debugging)."""
        return self.last_explanation
    
    def explanation_string(self, context, decision):
        """Quick single-line explanation for logging."""
        self.build(context, decision)
        return self.last_explanation["summary"]
