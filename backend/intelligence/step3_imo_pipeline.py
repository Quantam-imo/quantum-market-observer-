"""
Step 3 Integration — Full IMO Pipeline
Coordinates absorption detection → sweep detection → memory → IMO decision
This is the institutional execution brain
"""

from backend.intelligence.absorption_engine import AbsorptionEngine
from backend.intelligence.liquidity_sweep_engine import LiquiditySweepEngine
from backend.memory.iceberg_memory import IcebergMemoryEngine
from backend.intelligence.imo_engine import IMOEngine


class Step3IMOPipeline:
    """
    Complete institutional market observer pipeline.
    Processes raw CME trades → institutional decision framework
    """
    
    def __init__(self):
        self.absorption = AbsorptionEngine(threshold=400)
        self.sweeps = LiquiditySweepEngine()
        self.memory = IcebergMemoryEngine()
        self.imo = IMOEngine()
        self.execution_log = []
    
    def process_tick(self, tick_data, candle_data=None):
        """
        Process a single price tick with trade data.
        
        Args:
            tick_data: List of trades for this period {price, size, side, timestamp}
            candle_data: Optional OHLC candle for sweep detection
        
        Returns:
            IMO decision context
        """
        # Step 1: Detect absorption zones
        absorptions = self.absorption.detect(tick_data)
        
        # Step 2: Store new zones in memory
        for zone in absorptions:
            self.memory.store(zone)
        
        # Step 3: Detect sweeps (requires candlestick data)
        sweeps = []
        if candle_data:
            sweeps = self.sweeps.detect(candle_data)
            for sweep in sweeps:
                self.memory.store({
                    "price": sweep["level"],
                    "type": sweep["type"],
                    "volume": sweep.get("volume", 0),
                    "timestamp": sweep.get("time")
                })
        
        # Step 4: Get memory forecast
        current_price = tick_data[-1]["price"] if tick_data else 0
        memory_zones = self.memory.get_active_zones(current_price, tolerance=3)
        
        # Step 5: Evaluate with IMO
        context = {
            "absorption_zones": absorptions,
            "sweeps": sweeps,
            "current_price": current_price,
            "memory_zones": memory_zones,
            "volume": sum(t["size"] for t in tick_data) if tick_data else 0
        }
        
        decision = self.imo.evaluate(context)
        
        # Log execution
        self.execution_log.append({
            "timestamp": tick_data[-1].get("timestamp") if tick_data else None,
            "decision": decision,
            "absorption_count": len(absorptions),
            "sweep_count": len(sweeps),
            "memory_zones_active": len(memory_zones)
        })
        
        return decision
    
    def get_institutional_signal(self):
        """
        Return current institutional signal (human-readable).
        This is what the AI Mentor will communicate.
        """
        if not self.execution_log:
            return None
        
        latest = self.execution_log[-1]
        decision = latest["decision"]
        
        signal = {
            "decision": decision["decision"],
            "confidence": decision["confidence"],
            "institutional_interpretation": self._interpret_decision(decision),
            "zones_active": latest["absorption_count"],
            "traps_detected": latest["sweep_count"],
            "session_confluence": latest["memory_zones_active"],
            "recommendation": self._get_recommendation(decision)
        }
        
        return signal
    
    def _interpret_decision(self, decision):
        """Translate IMO score into institutional language."""
        if decision["decision"] == "EXECUTE":
            if decision["confidence"] > 0.85:
                return "High institutional conviction - strong setup"
            else:
                return "Institutional structure confirmed - ready for execution"
        elif decision["decision"] == "WAIT":
            return "Partial institutional signal - wait for stronger confirmation"
        else:
            return "Insufficient institutional structure - stay away"
    
    def _get_recommendation(self, decision):
        """Get trading recommendation based on structure."""
        if decision["score_breakdown"]["sweeps"] > 0.15:
            sweep_type = "BUY_SIDE" if any("BUY" in r for r in decision["reasons"]) else "SELL_SIDE"
            return f"Liquidity trapped on {sweep_type} - reentry likely opposite direction"
        
        if decision["score_breakdown"]["absorption"] > 0.2:
            return "Heavy absorption zone - institutions positioned, wait for breakout"
        
        return "Monitor structure for entry signal"
    
    def get_dashboard_data(self):
        """
        Comprehensive dashboard showing entire pipeline state.
        For frontend/monitoring.
        """
        latest_decision = self.imo.last_decision or {}
        memory_summary = self.memory.summary()
        
        return {
            "imo_decision": {
                "decision": latest_decision.get("decision", "NONE"),
                "confidence": latest_decision.get("confidence", 0),
                "score_breakdown": latest_decision.get("score_breakdown", {})
            },
            "memory": memory_summary,
            "recent_zones": self.memory.get_strong_zones(min_reuse=1)[:5],
            "sweep_history": self.sweeps.get_recent_sweeps(count=5),
            "decision_quality": self.imo.get_decision_quality(),
            "execution_count": len(self.execution_log),
            "imo_explanation": self.imo.explain_last_decision()
        }
    
    def reset_session(self):
        """Reset for new trading session while maintaining memory."""
        self.execution_log = []
        self.absorption = AbsorptionEngine(threshold=400)
        self.sweeps = LiquiditySweepEngine()
        # Memory persists across sessions intentionally


# Example usage for testing
if __name__ == "__main__":
    pipeline = Step3IMOPipeline()
    
    # Simulate tick data (example)
    sample_ticks = [
        {"price": 3362.4, "size": 48, "side": "BUY", "timestamp": "10:42:11"},
        {"price": 3362.5, "size": 52, "side": "BUY", "timestamp": "10:42:12"},
        {"price": 3362.4, "size": 45, "side": "SELL", "timestamp": "10:42:13"},
    ]
    
    # Simulate candle data (example)
    sample_candle = {
        "open": 3362.0,
        "high": 3365.5,
        "low": 3361.0,
        "close": 3363.0,
        "volume": 500,
        "time": "10:45:00"
    }
    
    # Process
    decision = pipeline.process_tick(sample_ticks, [sample_candle])
    print("\n" + pipeline.imo.explain_last_decision())
    print("\nDashboard:")
    print(pipeline.get_dashboard_data())
