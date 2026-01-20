# backtesting/signal_lifecycle.py
"""
SignalLifecycle: State machine for signal evolution.

Signals are not instant trades. They evolve through states:
- DORMANT: Potential forming (conditions emerging)
- ARMED: Conditions aligning (pre-entry)
- CONFIRMED: Trade allowed by filters
- ACTIVE: Trade entered, position live
- COMPLETED: Target hit or stop loss
- INVALIDATED: Failed before entry

This enables professional signal tracking and debugging.
"""


class SignalLifecycle:
    """State machine for signal evolution tracking."""
    
    STATES = [
        "DORMANT",
        "ARMED",
        "CONFIRMED",
        "ACTIVE",
        "COMPLETED",
        "INVALIDATED",
    ]
    
    def __init__(self):
        """Initialize with no active signal."""
        self.current_signal = None
        self.history = []
    
    def update(self, context, decision):
        """
        Update signal state based on decision.
        
        Args:
            context: Dict with session, killzone, news, iceberg_score, confidence
            decision: Dict with action/edge/confidence, or None
        
        Returns:
            Current signal state dict, or None if no active signal
        """
        # Case 1: No active signal, decision triggers one
        if not self.current_signal and decision:
            self.current_signal = {
                "state": "CONFIRMED",
                "action": decision.get("action"),
                "edge": decision.get("edge"),
                "confidence": decision.get("confidence", 0.0),
                "entry_price": context.get("price"),
                "entry_time": context.get("time"),
                "session": context.get("session"),
                "born_at": context.get("time"),
                "bars_alive": 0,
            }
            self.history.append(self.current_signal.copy())
            return self.current_signal
        
        # Case 2: Active signal exists
        if self.current_signal:
            # Increment lifetime
            self.current_signal["bars_alive"] += 1
            
            # Transition: CONFIRMED → ACTIVE (after first bar)
            if self.current_signal["state"] == "CONFIRMED" and self.current_signal["bars_alive"] >= 1:
                self.current_signal["state"] = "ACTIVE"
            
            # Check invalidation conditions
            if self._should_invalidate(context, decision):
                self.current_signal["state"] = "INVALIDATED"
                self.current_signal["invalidated_at"] = context.get("time")
                self.current_signal["reason"] = "conditions_failed"
                self.history.append(self.current_signal.copy())
                self.current_signal = None
                return self.current_signal
            
            # Check completion conditions (simplified)
            if self._should_complete(context, decision):
                self.current_signal["state"] = "COMPLETED"
                self.current_signal["completed_at"] = context.get("time")
                self.current_signal["exit_price"] = context.get("price")
                self.history.append(self.current_signal.copy())
                self.current_signal = None
                return self.current_signal
            
            # Update active signal metadata
            self.current_signal["current_price"] = context.get("price")
            self.current_signal["current_session"] = context.get("session")
            self.current_signal["current_confidence"] = context.get("confidence", 0.0)
            
            return self.current_signal
        
        return None
    
    def _should_invalidate(self, context, decision):
        """Check if signal should be invalidated."""
        # Signal invalidates if killzone blocks it
        if context.get("killzone"):
            return True
        
        # Signal invalidates if high-impact news appears after entry
        if context.get("news", {}).get("active") and context.get("news", {}).get("impact") == "HIGH":
            if self.current_signal and self.current_signal["bars_alive"] > 0:
                return True
        
        return False
    
    def _should_complete(self, context, decision):
        """Check if signal should be completed."""
        # Simplified: complete after 20 bars (actual implementation would track targets/stops)
        if self.current_signal and self.current_signal["bars_alive"] > 20:
            return True
        
        return False
    
    def is_active(self):
        """Return True if signal is currently active."""
        return self.current_signal is not None and self.current_signal["state"] == "ACTIVE"
    
    def get_current(self):
        """Return current signal state, or None."""
        return self.current_signal
    
    def get_history(self):
        """Return full signal history."""
        return self.history
    
    def reset(self):
        """Reset to initial state."""
        self.current_signal = None
        self.history = []
    
    def lifecycle_summary(self):
        """Return summary stats of signal lifecycle."""
        if not self.history:
            return {
                "total_signals": 0,
                "completed": 0,
                "invalidated": 0,
                "avg_bars_alive": 0,
            }
        
        completed = [s for s in self.history if s["state"] == "COMPLETED"]
        invalidated = [s for s in self.history if s["state"] == "INVALIDATED"]
        
        avg_bars = (
            sum(s["bars_alive"] for s in self.history) / len(self.history)
            if self.history
            else 0
        )
        
        return {
            "total_signals": len(self.history),
            "completed": len(completed),
            "invalidated": len(invalidated),
            "avg_bars_alive": avg_bars,
            "completion_rate": len(completed) / len(self.history) if self.history else 0,
        }
