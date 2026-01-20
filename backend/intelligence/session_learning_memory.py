"""
STEP 22: Session Learning Memory
Learns which setups work best in each trading session (Asia, London, NY)
"""

from typing import Dict, List
from datetime import datetime, time


class SessionLearningMemory:
    """
    Tracks setup performance per session.
    After 20-30 sessions, OIS knows which setups work best where.
    """

    def __init__(self):
        # Session definitions (24-hour format in UTC)
        self.sessions = {
            "Asia": {
                "start_hour": 22,  # Previous day 22:00 UTC
                "end_hour": 8,  # 08:00 UTC (next day)
                "timezone": "UTC",
            },
            "London": {
                "start_hour": 7,
                "end_hour": 16,
                "timezone": "UTC",
            },
            "NewYork": {
                "start_hour": 12,
                "end_hour": 21,
                "timezone": "UTC",
            },
        }

        # Performance memory per session
        self.session_memory: Dict[str, Dict] = {
            "Asia": self._init_session(),
            "London": self._init_session(),
            "NewYork": self._init_session(),
        }

    def _init_session(self) -> Dict:
        """Initialize empty session learning"""
        return {
            "best_setups": [],  # Setups with >70% win rate
            "failure_setups": [],  # Setups with <50% win rate
            "avg_follow_through": 0,  # Average pips after entry
            "best_time_entry": None,  # Best time within session
            "setup_performance": {
                "iceberg": {"wins": 0, "losses": 0},
                "gann_breakout": {"wins": 0, "losses": 0},
                "astro_aspect": {"wins": 0, "losses": 0},
                "cycle_inflection": {"wins": 0, "losses": 0},
                "liquidity_sweep": {"wins": 0, "losses": 0},
            },
            "total_trades": 0,
            "volatility_profile": "unknown",  # LOW / NORMAL / HIGH
            "last_updated": datetime.utcnow().isoformat(),
        }

    def get_current_session(self) -> str:
        """Determine current session based on UTC time"""
        now_utc = datetime.utcnow()
        hour = now_utc.hour

        # Check each session
        for session_name, session_info in self.sessions.items():
            start = session_info["start_hour"]
            end = session_info["end_hour"]

            if start < end:
                # Normal case (e.g., London 7-16)
                if start <= hour < end:
                    return session_name
            else:
                # Overnight case (e.g., Asia 22-8)
                if hour >= start or hour < end:
                    return session_name

        return "Unknown"

    def record_result(
        self,
        setup_name: str,
        win: bool,
        follow_through_pips: float = 0.0,
        session: str = None,
    ):
        """Record trade result for a setup in a session"""
        if session is None:
            session = self.get_current_session()

        if session not in self.session_memory:
            return

        session_data = self.session_memory[session]

        # Record setup performance
        if setup_name in session_data["setup_performance"]:
            setup = session_data["setup_performance"][setup_name]
            if win:
                setup["wins"] += 1
            else:
                setup["losses"] += 1

            session_data["total_trades"] += 1

            # Update average follow-through
            total_pips = (
                session_data["avg_follow_through"] * (session_data["total_trades"] - 1)
            )
            session_data["avg_follow_through"] = (
                total_pips + follow_through_pips
            ) / session_data["total_trades"]

            # Re-evaluate best/failure setups
            self._evaluate_session_setups(session)
            session_data["last_updated"] = datetime.utcnow().isoformat()

    def _evaluate_session_setups(self, session: str):
        """Determine best and failure setups for a session"""
        session_data = self.session_memory[session]
        best = []
        failure = []

        for setup_name, perf in session_data["setup_performance"].items():
            total = perf["wins"] + perf["losses"]
            if total < 5:  # Need at least 5 trades
                continue

            win_rate = perf["wins"] / total

            if win_rate > 0.70:
                best.append(setup_name)
            elif win_rate < 0.50:
                failure.append(setup_name)

        session_data["best_setups"] = best
        session_data["failure_setups"] = failure

    def get_setup_confidence_adjustment(self, setup_name: str, session: str = None) -> float:
        """
        Get confidence adjustment for a setup in a session.
        Positive = boost confidence, Negative = reduce confidence
        """
        if session is None:
            session = self.get_current_session()

        if session not in self.session_memory:
            return 0.0

        session_data = self.session_memory[session]

        # Boost best setups
        if setup_name in session_data["best_setups"]:
            return 0.08  # +8% confidence

        # Reduce failure setups
        if setup_name in session_data["failure_setups"]:
            return -0.08  # -8% confidence

        return 0.0

    def get_session_stats(self, session: str = None) -> Dict:
        """Get complete stats for a session"""
        if session is None:
            session = self.get_current_session()

        if session not in self.session_memory:
            return {}

        session_data = self.session_memory[session]
        total = session_data["total_trades"]

        win_rate = 0.0
        if total > 0:
            total_wins = sum(perf["wins"] for perf in session_data["setup_performance"].values())
            win_rate = total_wins / total

        return {
            "session": session,
            "total_trades": total,
            "overall_win_rate": win_rate,
            "best_setups": session_data["best_setups"],
            "failure_setups": session_data["failure_setups"],
            "avg_follow_through": session_data["avg_follow_through"],
            "setup_performance": session_data["setup_performance"],
            "volatility_profile": session_data["volatility_profile"],
            "last_updated": session_data["last_updated"],
        }

    def get_all_sessions_stats(self) -> Dict[str, Dict]:
        """Get stats for all sessions"""
        return {
            session: self.get_session_stats(session) for session in self.sessions.keys()
        }

    def set_session_volatility_profile(self, volatility: str, session: str = None):
        """Store volatility profile for a session"""
        if session is None:
            session = self.get_current_session()

        if session in self.session_memory:
            self.session_memory[session]["volatility_profile"] = volatility

    def export_state(self) -> Dict:
        """Export memory for persistence"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "sessions": self.session_memory,
        }

    def import_state(self, state: Dict):
        """Import memory from file"""
        if "sessions" in state:
            self.session_memory = state["sessions"]

    def reset_session(self, session: str):
        """Reset learning for a session (e.g., major market change)"""
        if session in self.session_memory:
            self.session_memory[session] = self._init_session()
