"""
Deployment Failsafe System
Hard stops that prevent crashes, bad signals, and cost explosions.
Runs on every signal generation.
"""

from datetime import datetime, timedelta
from enum import Enum
import json


class FailsafeState(Enum):
    """System health status."""
    HEALTHY = 1
    DEGRADED = 2
    UNSAFE = 3
    CRITICAL = 4


class DeploymentFailsafe:
    """
    Master failsafe controller.
    Every signal passes through this before reaching frontend.
    """
    
    def __init__(self):
        """Initialize failsafe system."""
        self.last_data_update = datetime.now()
        self.last_signal_time = None
        self.signals_today = 0
        self.last_news_event = None
        self.data_feed_status = "OK"
        self.api_call_count = 0
        self.last_hour_signals = 0
        self.consecutive_losses = 0
        self.health_log = []
        
        # Hard limits
        self.MAX_SIGNALS_PER_SESSION = 3  # 3 signals max per trading day
        self.MAX_SIGNALS_PER_HOUR = 1     # No more than 1 per hour
        self.MIN_CONFIDENCE = 0.70        # Must be 70%+ confidence
        self.NEWS_LOCKOUT_MINUTES = 15    # 15 min blackout after news
        self.MAX_API_CALLS_PER_MIN = 10   # Rate limit
        self.MAX_CONSECUTIVE_LOSSES = 3   # Stop trading after 3 losses
        self.DATA_STALE_MINUTES = 5       # Data older than 5 min = stale
    
    def check_all_failsafes(self, signal_data: dict) -> dict:
        """
        Run all failsafe checks.
        Returns: {
            "can_execute": bool,
            "reason": str,
            "state": FailsafeState,
            "warnings": [str]
        }
        """
        warnings = []
        
        # 1. Data Feed Check
        if not self._check_data_feed():
            return {
                "can_execute": False,
                "reason": "❌ DATA FEED MISSING — No valid price data",
                "state": FailsafeState.CRITICAL,
                "warnings": ["All signals disabled until data restored"]
            }
        
        # 2. News Lockout Check
        if self._is_news_lockout():
            return {
                "can_execute": False,
                "reason": "🔴 NEWS BLACKOUT — High impact event < 15 min",
                "state": FailsafeState.UNSAFE,
                "warnings": ["Switching to OBSERVE mode until lockout expires"]
            }
        
        # 3. Confidence Floor Check
        confidence = signal_data.get("confidence", 0.0)
        if confidence < self.MIN_CONFIDENCE:
            return {
                "can_execute": False,
                "reason": f"⚠️ LOW CONFIDENCE ({confidence:.1%}) — Below {self.MIN_CONFIDENCE:.0%} threshold",
                "state": FailsafeState.UNSAFE,
                "warnings": [f"Need {self.MIN_CONFIDENCE:.0%}+ confidence. Skipping signal."]
            }
        
        # 4. Signal Frequency Check
        if self._exceeds_signal_frequency():
            return {
                "can_execute": False,
                "reason": f"⏰ SIGNAL LIMIT REACHED — {self.signals_today} signals today (max {self.MAX_SIGNALS_PER_SESSION})",
                "state": FailsafeState.DEGRADED,
                "warnings": ["Max signals per session reached. Come back tomorrow."]
            }
        
        # 5. Hourly Rate Limit Check
        if self._exceeds_hourly_rate():
            return {
                "can_execute": False,
                "reason": f"⏱️ RATE LIMIT — Too many signals this hour",
                "state": FailsafeState.DEGRADED,
                "warnings": ["Only 1 signal per hour allowed. Try again later."]
            }
        
        # 6. API Call Rate Check
        if self._exceeds_api_rate():
            return {
                "can_execute": False,
                "reason": "🚫 API RATE EXCEEDED — Cost control triggered",
                "state": FailsafeState.CRITICAL,
                "warnings": ["API rate limit hit. System cooldown active."]
            }
        
        # 7. Loss Prevention Check
        if self._stop_trading_after_losses():
            return {
                "can_execute": False,
                "reason": f"🛑 LOSS PROTECTION — {self.consecutive_losses} losses. Taking a break.",
                "state": FailsafeState.DEGRADED,
                "warnings": [
                    f"{self.consecutive_losses} losses detected.",
                    "Psychology protection activated. Rest required."
                ]
            }
        
        # All checks passed
        self._log_health("HEALTHY", "All failsafes passed")
        return {
            "can_execute": True,
            "reason": "✅ APPROVED — All safety checks passed",
            "state": FailsafeState.HEALTHY,
            "warnings": []
        }
    
    def _check_data_feed(self) -> bool:
        """Check if price data is current."""
        time_since_update = datetime.now() - self.last_data_update
        is_stale = time_since_update.total_seconds() > (self.DATA_STALE_MINUTES * 60)
        
        if is_stale or self.data_feed_status != "OK":
            self._log_health("CRITICAL", f"Data stale or missing: {self.data_feed_status}")
            return False
        
        return True
    
    def _is_news_lockout(self) -> bool:
        """Check if high-impact news just happened."""
        if not self.last_news_event:
            return False
        
        time_since_news = datetime.now() - self.last_news_event
        lockout_expired = time_since_news.total_seconds() > (self.NEWS_LOCKOUT_MINUTES * 60)
        
        if not lockout_expired:
            self._log_health("UNSAFE", f"News lockout active: {self.NEWS_LOCKOUT_MINUTES} min")
            return True
        
        return False
    
    def _exceeds_signal_frequency(self) -> bool:
        """Check if we've hit max signals per session."""
        if self.signals_today >= self.MAX_SIGNALS_PER_SESSION:
            self._log_health("DEGRADED", f"Max signals/session: {self.signals_today}")
            return True
        return False
    
    def _exceeds_hourly_rate(self) -> bool:
        """Check if we've exceeded 1 signal per hour."""
        if self.last_hour_signals >= self.MAX_SIGNALS_PER_HOUR:
            self._log_health("DEGRADED", "Hourly rate limit hit")
            return True
        return False
    
    def _exceeds_api_rate(self) -> bool:
        """Check if API calls exceed rate limit."""
        if self.api_call_count >= self.MAX_API_CALLS_PER_MIN:
            self._log_health("CRITICAL", "API rate exceeded")
            return True
        return False
    
    def _stop_trading_after_losses(self) -> bool:
        """Stop trading after N consecutive losses."""
        if self.consecutive_losses >= self.MAX_CONSECUTIVE_LOSSES:
            self._log_health("DEGRADED", f"Loss protection: {self.consecutive_losses} losses")
            return True
        return False
    
    def record_signal(self, signal_data: dict, executed: bool):
        """Record signal for rate limiting tracking."""
        self.signals_today += 1
        self.last_signal_time = datetime.now()
        self.last_hour_signals += 1
        
        self._log_health("SIGNAL", f"Signal #{self.signals_today} recorded")
    
    def record_trade_result(self, result: str):
        """Update loss counter for psychology protection."""
        if result == "LOSS":
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0  # Reset on win
    
    def record_news_event(self, impact: str):
        """Mark high-impact news occurred."""
        if impact in ["HIGH", "MEDIUM"]:
            self.last_news_event = datetime.now()
            self._log_health("NEWS", f"{impact} impact news event")
    
    def update_data_feed_status(self, status: str):
        """Update data feed health."""
        self.data_feed_status = status
        self.last_data_update = datetime.now()
        
        if status == "OK":
            self._log_health("DATA", "Price feed healthy")
        else:
            self._log_health("CRITICAL", f"Price feed error: {status}")
    
    def reset_hourly_counter(self):
        """Call every hour to reset hourly signal count."""
        self.last_hour_signals = 0
    
    def reset_daily_counters(self):
        """Call at market open (9:30 AM) to reset daily limits."""
        self.signals_today = 0
        self.consecutive_losses = 0
        self._log_health("DAILY_RESET", "Counters reset for new session")
    
    def _log_health(self, event_type: str, message: str):
        """Log system health event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "signals_today": self.signals_today,
            "losses": self.consecutive_losses,
            "data_status": self.data_feed_status
        }
        
        self.health_log.append(log_entry)
        
        # Keep last 1000 entries
        if len(self.health_log) > 1000:
            self.health_log = self.health_log[-1000:]
    
    def get_health_status(self) -> dict:
        """Get current system health."""
        return {
            "data_feed": self.data_feed_status,
            "signals_today": f"{self.signals_today}/{self.MAX_SIGNALS_PER_SESSION}",
            "consecutive_losses": self.consecutive_losses,
            "last_signal": self.last_signal_time.isoformat() if self.last_signal_time else "None",
            "in_news_lockout": self._is_news_lockout(),
            "recent_events": self.health_log[-5:]  # Last 5 events
        }
    
    def print_dashboard(self):
        """Print system health dashboard."""
        print("\n" + "="*70)
        print("DEPLOYMENT FAILSAFE DASHBOARD")
        print("="*70 + "\n")
        
        health = self.get_health_status()
        
        print(f"📊 DATA FEED:        {health['data_feed']}")
        print(f"📈 SIGNALS TODAY:    {health['signals_today']}")
        print(f"📉 CONSECUTIVE LOSS: {health['consecutive_losses']}")
        print(f"⏰ LAST SIGNAL:      {health['last_signal']}")
        print(f"🔴 NEWS LOCKOUT:     {'YES' if health['in_news_lockout'] else 'NO'}\n")
        
        print("Recent Events:")
        for event in health['recent_events']:
            print(f"  {event['timestamp'][:19]} | {event['type']:12} | {event['message']}")
        
        print("\n" + "="*70 + "\n")


# Example usage:
if __name__ == "__main__":
    failsafe = DeploymentFailsafe()
    
    # Simulate healthy signal
    print("TEST 1: Healthy signal")
    signal = {"confidence": 0.85, "direction": "SELL"}
    result = failsafe.check_all_failsafes(signal)
    print(f"  Result: {result['reason']}\n")
    
    # Simulate low confidence
    print("TEST 2: Low confidence signal")
    signal = {"confidence": 0.55, "direction": "BUY"}
    result = failsafe.check_all_failsafes(signal)
    print(f"  Result: {result['reason']}\n")
    
    # Simulate data feed missing
    print("TEST 3: Stale data feed")
    failsafe.update_data_feed_status("STALE")
    result = failsafe.check_all_failsafes(signal)
    print(f"  Result: {result['reason']}\n")
    
    # Restore and test news lockout
    print("TEST 4: News lockout active")
    failsafe.update_data_feed_status("OK")
    failsafe.record_news_event("HIGH")
    signal = {"confidence": 0.85, "direction": "SELL"}
    result = failsafe.check_all_failsafes(signal)
    print(f"  Result: {result['reason']}\n")
    
    # Print dashboard
    failsafe.print_dashboard()
