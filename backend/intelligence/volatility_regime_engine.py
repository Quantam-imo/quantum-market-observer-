"""
STEP 22: Volatility Regime Engine
Adapts trading behavior based on market volatility state (LOW/NORMAL/HIGH/EXTREME)
"""

from typing import Dict, List
from datetime import datetime, timedelta
from collections import deque


class VolatilityRegimeEngine:
    """
    Monitors volatility and classifies market regime.
    Adapts OIS behavior (position size, stop width, confirmation requirements) per regime.
    """

    def __init__(self, lookback_periods: int = 20):
        self.lookback_periods = lookback_periods
        self.ranges = deque(maxlen=lookback_periods)

        # Regime states
        self.current_regime = "NORMAL"
        self.previous_regime = "NORMAL"
        self.regime_change_time = datetime.utcnow()

        # Thresholds for regime classification
        self.vol_thresholds = {
            "EXTREME": 1.8,  # ratio > 1.8x average
            "HIGH": 1.4,  # ratio 1.4-1.8x
            "NORMAL": 1.0,  # ratio 0.7-1.4x
            "LOW": 0.7,  # ratio < 0.7x
        }

        # Behavioral adjustments per regime
        self.regime_actions = {
            "LOW": {
                "position_size_multiplier": 0.6,  # 40% smaller positions
                "stop_width_multiplier": 1.2,  # 20% wider stops (less noise)
                "confirmation_requirements": 3,  # Require 3+ confluences
                "trade_enabled": True,
                "risk_reduction": 0.0,
            },
            "NORMAL": {
                "position_size_multiplier": 1.0,  # Standard size
                "stop_width_multiplier": 1.0,  # Standard stops
                "confirmation_requirements": 2,  # 2+ confluences
                "trade_enabled": True,
                "risk_reduction": 0.0,
            },
            "HIGH": {
                "position_size_multiplier": 0.7,  # 30% smaller
                "stop_width_multiplier": 1.3,  # 30% wider stops
                "confirmation_requirements": 3,  # Require more confluence
                "trade_enabled": True,
                "risk_reduction": 0.10,  # Reduce confidence by 10%
            },
            "EXTREME": {
                "position_size_multiplier": 0.3,  # 70% smaller (crisis mode)
                "stop_width_multiplier": 1.5,  # Very wide stops
                "confirmation_requirements": 4,  # Require 4+ confluences
                "trade_enabled": False,  # Disable execution on extreme vol
                "risk_reduction": 0.30,  # Reduce confidence by 30%
            },
        }

    def update(self, high: float, low: float, close: float) -> str:
        """
        Update with new bar. Returns current regime.
        """
        # Calculate range
        bar_range = high - low

        # Store range
        self.ranges.append(bar_range)

        # Calculate regime
        if len(self.ranges) >= self.lookback_periods:
            avg_range = sum(self.ranges) / len(self.ranges)
            vol_ratio = bar_range / avg_range if avg_range > 0 else 1.0

            # Classify regime
            self.previous_regime = self.current_regime

            if vol_ratio > self.vol_thresholds["EXTREME"]:
                self.current_regime = "EXTREME"
            elif vol_ratio > self.vol_thresholds["HIGH"]:
                self.current_regime = "HIGH"
            elif vol_ratio < self.vol_thresholds["LOW"]:
                self.current_regime = "LOW"
            else:
                self.current_regime = "NORMAL"

            # Track regime changes
            if self.current_regime != self.previous_regime:
                self.regime_change_time = datetime.utcnow()

        return self.current_regime

    def get_regime(self) -> str:
        """Get current regime"""
        return self.current_regime

    def is_regime_change(self) -> bool:
        """Did regime just change?"""
        return self.current_regime != self.previous_regime

    def get_regime_age_seconds(self) -> float:
        """How long (seconds) have we been in current regime?"""
        delta = datetime.utcnow() - self.regime_change_time
        return delta.total_seconds()

    def get_position_size_multiplier(self) -> float:
        """Position size adjustment for current regime"""
        return self.regime_actions[self.current_regime]["position_size_multiplier"]

    def get_stop_width_multiplier(self) -> float:
        """Stop width adjustment for current regime"""
        return self.regime_actions[self.current_regime]["stop_width_multiplier"]

    def get_confirmation_requirements(self) -> int:
        """How many confluences required in current regime?"""
        return self.regime_actions[self.current_regime]["confirmation_requirements"]

    def is_trading_enabled(self) -> bool:
        """Should trading be enabled in current regime?"""
        return self.regime_actions[self.current_regime]["trade_enabled"]

    def get_risk_reduction(self) -> float:
        """Confidence reduction to apply (0.0 to 0.30)"""
        return self.regime_actions[self.current_regime]["risk_reduction"]

    def get_regime_description(self) -> str:
        """Human-readable regime description"""
        descriptions = {
            "LOW": "Low Volatility - Compression, require strong confluence",
            "NORMAL": "Normal Volatility - Standard trading rules apply",
            "HIGH": "High Volatility - Wider stops, smaller size, extra confirmation",
            "EXTREME": "Extreme Volatility - Trading disabled, capital protection",
        }
        return descriptions.get(self.current_regime, "Unknown")

    def get_all_regime_stats(self) -> Dict:
        """Get complete regime statistics"""
        avg_range = sum(self.ranges) / len(self.ranges) if self.ranges else 0.0
        current_range = self.ranges[-1] if self.ranges else 0.0
        vol_ratio = current_range / avg_range if avg_range > 0 else 0.0

        return {
            "regime": self.current_regime,
            "previous_regime": self.previous_regime,
            "is_change": self.is_regime_change(),
            "regime_age_seconds": self.get_regime_age_seconds(),
            "vol_ratio": vol_ratio,
            "avg_range": avg_range,
            "current_range": current_range,
            "bars_sampled": len(self.ranges),
            "position_size_multiplier": self.get_position_size_multiplier(),
            "stop_width_multiplier": self.get_stop_width_multiplier(),
            "confirmation_requirements": self.get_confirmation_requirements(),
            "trading_enabled": self.is_trading_enabled(),
            "risk_reduction": self.get_risk_reduction(),
            "description": self.get_regime_description(),
        }

    def export_state(self) -> Dict:
        """Export current state for persistence"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_regime": self.current_regime,
            "previous_regime": self.previous_regime,
            "ranges": list(self.ranges),
            "regime_change_time": self.regime_change_time.isoformat(),
        }

    def import_state(self, state: Dict):
        """Import state from file"""
        if "current_regime" in state:
            self.current_regime = state["current_regime"]
        if "previous_regime" in state:
            self.previous_regime = state["previous_regime"]
        if "ranges" in state:
            self.ranges = deque(state["ranges"], maxlen=self.lookback_periods)
        if "regime_change_time" in state:
            self.regime_change_time = datetime.fromisoformat(state["regime_change_time"])
