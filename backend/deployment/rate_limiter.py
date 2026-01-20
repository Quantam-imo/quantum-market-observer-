"""
Rate Limiting & Cost Control
Prevents API explosion, keeps costs predictable.
Enforces scan frequencies per engine.
"""

from datetime import datetime, timedelta
from enum import Enum


class ScanFrequency(Enum):
    """How often each engine should run."""
    QMO = 20  # Every 20 minutes (3 times per hour)
    GANN = "session"  # Once per session, session-based
    ASTRO = "precalc"  # Pre-calculated, no live scanning
    CYCLES = "bar"  # Once per candle close
    ICEBERG = "event"  # Only on large volume events
    NEWS = 300  # Every 5 minutes (cache)
    CONFIDENCE = "state_change"  # Only when state changes


class RateLimiter:
    """
    Prevents API calls from exploding costs.
    Enforces smart scan frequencies.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self.last_scan = {}
        self.call_counts = {}
        self.cost_estimate = 0.0
        
        # Initialize scan times
        self.last_scan["qmo"] = datetime.now()
        self.last_scan["gann"] = datetime.now()
        self.last_scan["astro"] = datetime.now()
        self.last_scan["cycles"] = datetime.now()
        self.last_scan["iceberg"] = datetime.now()
        self.last_scan["news"] = datetime.now()
        
        # Cost per API call (example: CME data calls)
        self.costs = {
            "qmo": 0.00,  # Free (derived)
            "gann": 0.00,  # Free (calculated)
            "astro": 0.00,  # Free (pre-calculated)
            "cycles": 0.00,  # Free (local)
            "iceberg": 0.01,  # $0.01 per large volume event
            "news": 0.001,  # $0.001 per cached fetch
            "cme_api_call": 0.05,  # $0.05 per real API call
        }
    
    def can_run_engine(self, engine_name: str) -> bool:
        """
        Check if engine can run right now.
        
        Returns True only if enough time has passed since last run.
        """
        engine = engine_name.lower()
        
        if engine == "qmo":
            return self._can_run_qmo()
        elif engine == "gann":
            return self._can_run_gann()
        elif engine == "astro":
            return self._can_run_astro()
        elif engine == "cycles":
            return self._can_run_cycles()
        elif engine == "iceberg":
            return True  # Event-driven, always check
        elif engine == "news":
            return self._can_run_news()
        
        return False
    
    def _can_run_qmo(self) -> bool:
        """QMO should run every 15-30 minutes, not every tick."""
        time_since_last = datetime.now() - self.last_scan["qmo"]
        min_interval = timedelta(minutes=20)
        
        if time_since_last >= min_interval:
            self.last_scan["qmo"] = datetime.now()
            self._record_cost("qmo", 0.00)
            return True
        
        return False
    
    def _can_run_gann(self) -> bool:
        """Gann levels change per session, not per tick."""
        # Gann runs once per session (e.g., 9:30 AM ET)
        # This is session-based, not time-based
        # For now, allow once per hour to catch new sessions
        time_since_last = datetime.now() - self.last_scan["gann"]
        min_interval = timedelta(hours=1)
        
        if time_since_last >= min_interval:
            self.last_scan["gann"] = datetime.now()
            self._record_cost("gann", 0.00)
            return True
        
        return False
    
    def _can_run_astro(self) -> bool:
        """Astro aspects are pre-calculated, run once daily at startup."""
        # In production: pre-calculate at market open, never again
        # For testing: once per day
        time_since_last = datetime.now() - self.last_scan["astro"]
        min_interval = timedelta(hours=24)
        
        if time_since_last >= min_interval:
            self.last_scan["astro"] = datetime.now()
            self._record_cost("astro", 0.00)
            return True
        
        # Astro aspects rarely change during session
        return False
    
    def _can_run_cycles(self) -> bool:
        """Cycles run once per bar close."""
        # Cycles are bar-based, not time-based
        # Allow once per 5-minute candle close
        time_since_last = datetime.now() - self.last_scan["cycles"]
        min_interval = timedelta(minutes=5)
        
        if time_since_last >= min_interval:
            self.last_scan["cycles"] = datetime.now()
            self._record_cost("cycles", 0.00)
            return True
        
        return False
    
    def _can_run_news(self) -> bool:
        """News calendar: cache every 5 minutes, don't fetch on every tick."""
        time_since_last = datetime.now() - self.last_scan["news"]
        min_interval = timedelta(minutes=5)  # Cache interval
        
        if time_since_last >= min_interval:
            self.last_scan["news"] = datetime.now()
            # Cost depends on source
            # ForexFactory cached: $0.001 per call
            # Real-time feed: higher cost
            self._record_cost("news", 0.001)
            return True
        
        return False
    
    def record_iceberg_check(self, large_volume_detected: bool):
        """Record iceberg detection (event-driven)."""
        if large_volume_detected:
            self._record_cost("iceberg", 0.01)
    
    def _record_cost(self, operation: str, cost: float):
        """Record API cost."""
        if operation not in self.call_counts:
            self.call_counts[operation] = {"count": 0, "cost": 0.0}
        
        self.call_counts[operation]["count"] += 1
        self.call_counts[operation]["cost"] += cost
        self.cost_estimate += cost
    
    def get_cost_summary(self) -> dict:
        """Get current cost breakdown."""
        return {
            "total_cost": f"${self.cost_estimate:.2f}",
            "by_operation": self.call_counts,
            "projected_daily": f"${self.cost_estimate * 1440:.2f}",  # If rate continues
            "projected_monthly": f"${self.cost_estimate * 43200:.2f}"
        }
    
    def print_scan_schedule(self):
        """Print when each engine should run."""
        print("\n" + "="*70)
        print("ENGINE SCAN SCHEDULE (Cost Control)")
        print("="*70 + "\n")
        
        print("Engine         Frequency        Cost/Call    Purpose")
        print("-" * 70)
        print("QMO            Every 20 min     $0.00        Market phase")
        print("GANN           Per session      $0.00        Price levels")
        print("ASTRO          Daily (cached)   $0.00        Timing windows")
        print("CYCLES         Per candle       $0.00        Bar counts")
        print("ICEBERG        On large vol     $0.01/event  Absorption")
        print("NEWS           Every 5 min      $0.001/call  High impact events")
        
        print("\n" + "="*70)
        print(f"\nEstimated Monthly Cost: {self.get_cost_summary()['projected_monthly']}")
        print("(Far below $100 for professional trader account)")
        print("="*70 + "\n")


# Example usage:
if __name__ == "__main__":
    limiter = RateLimiter()
    
    # Print schedule
    limiter.print_scan_schedule()
    
    # Test scan frequency
    print("TEST: Checking if engines can run\n")
    
    print(f"QMO can run?    {limiter.can_run_engine('qmo')} (first time)")
    print(f"GANN can run?   {limiter.can_run_engine('gann')} (first time)")
    print(f"NEWS can run?   {limiter.can_run_engine('news')} (first time)")
    
    # Try again immediately
    print(f"\nQMO can run again? {limiter.can_run_engine('qmo')} (too soon)")
    print(f"GANN can run again? {limiter.can_run_engine('gann')} (too soon)")
    
    # Show cost
    print(f"\nCost Summary:")
    print(limiter.get_cost_summary())
