"""
STEP 22: Capital Protection Engine
Session locking, drawdown management, and adaptive risk reduction
"""

from typing import Dict, List
from datetime import datetime, timedelta
from collections import deque


class CapitalProtectionEngine:
    """
    Protects capital through intelligent session/daily management.
    Features:
    - Session lock after 2 consecutive losses
    - Daily drawdown limits (stop if DD > X%)
    - Weekly drawdown monitoring
    - Consecutive loss tracking
    """

    def __init__(self, account_size: float = 10000.0):
        self.account_size = account_size
        self.starting_balance = account_size

        # Session management
        self.session_locked = False
        self.session_loss_count = 0
        self.session_loss_limit = 2  # Lock after 2 losses
        self.session_start_time = datetime.utcnow()

        # Daily management
        self.daily_pnl = 0.0
        self.daily_loss_limit = account_size * 0.05  # 5% daily loss limit
        self.daily_start_balance = account_size
        self.daily_start_time = datetime.utcnow()

        # Weekly management
        self.weekly_pnl = 0.0
        self.weekly_loss_limit = account_size * 0.10  # 10% weekly loss limit
        self.weekly_start_balance = account_size
        self.weekly_start_time = datetime.utcnow()

        # Drawdown tracking
        self.peak_balance = account_size
        self.current_drawdown_percent = 0.0
        self.max_drawdown_percent = 0.0

        # Trade history
        self.trades: deque = deque(maxlen=50)

        # Risk reduction state
        self.risk_reduction_active = False
        self.risk_reduction_factor = 1.0

    def record_trade(self, pnl: float):
        """Record a trade result"""
        current_balance = self.starting_balance + sum(t["pnl"] for t in self.trades) + pnl

        # Update peak balance for drawdown calc
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

        # Calculate drawdowns
        self.current_drawdown_percent = ((self.peak_balance - current_balance) / self.peak_balance * 100)
        if self.current_drawdown_percent > self.max_drawdown_percent:
            self.max_drawdown_percent = self.current_drawdown_percent

        # Update periods
        self.daily_pnl += pnl
        self.weekly_pnl += pnl

        # Track session losses
        if pnl < 0:
            self.session_loss_count += 1
        else:
            self.session_loss_count = 0

        # Store trade
        self.trades.append({
            "pnl": pnl,
            "timestamp": datetime.utcnow().isoformat(),
            "balance": current_balance,
        })

        # Check protection rules
        self._evaluate_protection_rules()

    def _evaluate_protection_rules(self):
        """Check if any protection rules should be triggered"""
        current_balance = self.starting_balance + sum(t["pnl"] for t in self.trades)

        # Rule 1: Session loss limit
        if self.session_loss_count >= self.session_loss_limit:
            self.session_locked = True

        # Rule 2: Daily loss limit
        if self.daily_pnl < -self.daily_loss_limit:
            self.risk_reduction_active = True
            self.risk_reduction_factor = 0.5  # 50% risk reduction

        # Rule 3: Weekly loss limit
        if self.weekly_pnl < -self.weekly_loss_limit:
            self.risk_reduction_active = True
            self.risk_reduction_factor = 0.25  # 75% risk reduction

    def is_session_locked(self) -> bool:
        """Is current session locked (stop trading)?"""
        return self.session_locked

    def is_risk_reduced(self) -> bool:
        """Is risk reduction active?"""
        return self.risk_reduction_active

    def get_risk_reduction_factor(self) -> float:
        """Get position size multiplier (1.0 = normal, 0.5 = 50% size)"""
        return self.risk_reduction_factor

    def reset_session(self):
        """Reset session-level counters"""
        self.session_locked = False
        self.session_loss_count = 0
        self.session_start_time = datetime.utcnow()

    def reset_daily(self):
        """Reset daily counters and recalculate"""
        self.daily_pnl = 0.0
        self.daily_start_time = datetime.utcnow()
        self.daily_start_balance = self.starting_balance + sum(t["pnl"] for t in self.trades)

        # Clear risk reduction if conditions met
        if self.daily_pnl > 0:
            self.risk_reduction_active = False
            self.risk_reduction_factor = 1.0

    def reset_weekly(self):
        """Reset weekly counters and recalculate"""
        self.weekly_pnl = 0.0
        self.weekly_start_time = datetime.utcnow()
        self.weekly_start_balance = self.starting_balance + sum(t["pnl"] for t in self.trades)

        # Clear risk reduction if conditions met
        if self.weekly_pnl > 0:
            self.risk_reduction_active = False
            self.risk_reduction_factor = 1.0

    def get_protection_status(self) -> Dict:
        """Get complete protection status"""
        current_balance = self.starting_balance + sum(t["pnl"] for t in self.trades)
        total_pnl = current_balance - self.starting_balance

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "account_size": self.account_size,
            "current_balance": current_balance,
            "total_pnl": total_pnl,
            "total_pnl_percent": (total_pnl / self.account_size * 100) if self.account_size > 0 else 0,
            "daily_pnl": self.daily_pnl,
            "daily_limit": self.daily_loss_limit,
            "daily_remaining": self.daily_loss_limit + self.daily_pnl,
            "weekly_pnl": self.weekly_pnl,
            "weekly_limit": self.weekly_loss_limit,
            "weekly_remaining": self.weekly_loss_limit + self.weekly_pnl,
            "drawdown_percent": self.current_drawdown_percent,
            "max_drawdown_percent": self.max_drawdown_percent,
            "session_locked": self.session_locked,
            "session_losses": self.session_loss_count,
            "risk_reduction_active": self.risk_reduction_active,
            "risk_reduction_factor": self.risk_reduction_factor,
            "peak_balance": self.peak_balance,
            "total_trades": len(self.trades),
        }

    def get_consecutive_losses(self) -> int:
        """Get current consecutive loss count"""
        return self.session_loss_count

    def should_trade(self) -> bool:
        """Should we be trading right now?"""
        return not self.session_locked and not (self.risk_reduction_active and self.risk_reduction_factor < 0.5)

    def export_state(self) -> Dict:
        """Export for persistence"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "account_size": self.account_size,
            "starting_balance": self.starting_balance,
            "daily_pnl": self.daily_pnl,
            "weekly_pnl": self.weekly_pnl,
            "peak_balance": self.peak_balance,
            "current_drawdown_percent": self.current_drawdown_percent,
            "max_drawdown_percent": self.max_drawdown_percent,
            "session_locked": self.session_locked,
            "session_loss_count": self.session_loss_count,
            "risk_reduction_active": self.risk_reduction_active,
            "risk_reduction_factor": self.risk_reduction_factor,
            "trades": list(self.trades),
        }

    def import_state(self, state: Dict):
        """Import state from file"""
        if "account_size" in state:
            self.account_size = state["account_size"]
        if "starting_balance" in state:
            self.starting_balance = state["starting_balance"]
        if "daily_pnl" in state:
            self.daily_pnl = state["daily_pnl"]
        if "weekly_pnl" in state:
            self.weekly_pnl = state["weekly_pnl"]
        if "peak_balance" in state:
            self.peak_balance = state["peak_balance"]
        if "current_drawdown_percent" in state:
            self.current_drawdown_percent = state["current_drawdown_percent"]
        if "max_drawdown_percent" in state:
            self.max_drawdown_percent = state["max_drawdown_percent"]
        if "session_locked" in state:
            self.session_locked = state["session_locked"]
        if "session_loss_count" in state:
            self.session_loss_count = state["session_loss_count"]
        if "risk_reduction_active" in state:
            self.risk_reduction_active = state["risk_reduction_active"]
        if "risk_reduction_factor" in state:
            self.risk_reduction_factor = state["risk_reduction_factor"]
        if "trades" in state:
            self.trades = deque(state["trades"], maxlen=50)
