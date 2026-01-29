"""
Mentor Brain — adaptive decision layer

Bridges core signals with adaptive learning engines (edge decay, volatility,
session learning, news learning, capital protection). Kept intentionally
lightweight for testability; business logic lives in the individual engines.
"""

from typing import Dict, Any

from backend.intelligence.edge_decay_engine import EdgeDecayEngine
from backend.intelligence.volatility_regime_engine import VolatilityRegimeEngine
from backend.intelligence.session_learning_memory import SessionLearningMemory
from backend.intelligence.news_learning_engine import NewsImpactLearningEngine
from backend.intelligence.capital_protection_engine import CapitalProtectionEngine


class MentorBrain:
    def __init__(self, account_size: float = 10000.0):
        self.account_size = account_size

        # Adaptive learning components
        self.edge_decay = EdgeDecayEngine()
        self.volatility_regime = VolatilityRegimeEngine()
        self.session_learning = SessionLearningMemory()
        self.news_learning = NewsImpactLearningEngine()
        self.capital_protection = CapitalProtectionEngine(account_size=account_size)

    def decide(self, ctx: Dict[str, Any]):
        """Gatekeeper for execution decisions with adaptive guards."""
        if not ctx.get("qmo") or not ctx.get("imo"):
            return None

        # Base confidence gate
        if ctx.get("confidence", 0) < 0.7:
            return None

        # Capital protection can outright block trading
        if self.capital_protection.is_session_locked() or not self.capital_protection.should_trade():
            return None

        # Volatility regime requirements
        required_confirms = self.volatility_regime.get_confirmation_requirements()
        provided_confirms = ctx.get("confirmations", 0)

        # If confirmations are insufficient, signal WAIT but include requirement
        if provided_confirms < required_confirms:
            return {
                "decision": "WAIT",
                "required_confirmations": required_confirms,
                "regime": self.volatility_regime.get_regime(),
            }

        # Apply risk reduction if active
        risk_factor = self.capital_protection.get_risk_reduction_factor()

        return {
            "decision": "EXECUTE",
            "confidence": int(ctx.get("confidence", 0) * 100),
            "required_confirmations": required_confirms,
            "regime": self.volatility_regime.get_regime(),
            "risk_reduction": risk_factor,
        }

    def record_trade_result(
        self,
        setup_type: str,
        win: bool,
        pnl: float = 0.0,
        follow_through_pips: float = 0.0,
        session: str = None,
    ):
        """Log a trade outcome across all adaptive engines."""
        self.edge_decay.record_result(setup_type, win, {"pnl": pnl})
        self.session_learning.record_result(
            setup_name=setup_type,
            win=win,
            follow_through_pips=follow_through_pips,
            session=session,
        )
        self.capital_protection.record_trade(pnl)

    def record_news_event(
        self,
        news_type: str,
        reaction: str,
        initial_range_pips: float,
        total_range_pips: float,
        time_to_reversal_minutes: float = 0,
        direction: str = "UP",
        impact_level: str = "HIGH",
    ):
        """Log a news reaction for adaptive adjustments."""
        self.news_learning.record_news_event(
            news_type=news_type,
            reaction=reaction,
            initial_range_pips=initial_range_pips,
            total_range_pips=total_range_pips,
            time_to_reversal_minutes=time_to_reversal_minutes,
            direction=direction,
            impact_level=impact_level,
        )

    def get_adaptive_status(self) -> Dict[str, Any]:
        """Snapshot of all adaptive engines for dashboards/tests."""
        return {
            "edge_decay": self.edge_decay.get_all_decays(),
            "volatility": self.volatility_regime.get_all_regime_stats(),
            "session_learning": self.session_learning.get_all_sessions_stats(),
            "news_learning": self.news_learning.get_news_stats(),
            "capital_protection": self.capital_protection.get_protection_status(),
        }
