# backtesting/chart_packet_builder.py
"""
ChartPacketBuilder: Produces clean, chart-ready data packets.

This is the interface between backtesting (internal) and UI (future).
- Safe data (no internal state leakage)
- Time-aligned (ISO format)
- Signal-annotated (buy/sell/skip)
- Confidence-tagged (how much to trust it)
"""


class ChartPacketBuilder:
    """Converts internal replay state → clean chart data packets."""
    
    def __init__(self):
        """Initialize packet builder."""
        self.packets = []
    
    def build(self, candle, context, decision, explanation=None):
        """
        Create single chart-ready packet.
        
        Args:
            candle: Dict with time, open, high, low, close, volume (optional)
            context: Dict with session, killzone, iceberg_score, confidence
            decision: Dict with action/edge/confidence, or None
            explanation: Optional dict from ExplanationEngine
        
        Returns:
            Dict ready for chart consumption
        """
        # Convert time to ISO format if needed
        time_str = (
            candle["time"].isoformat()
            if hasattr(candle["time"], "isoformat")
            else str(candle["time"])
        )
        
        # Extract decision signal
        signal = None
        signal_edge = None
        signal_confidence = 0.0
        
        if decision:
            signal = decision.get("action", "UNKNOWN").upper()
            signal_edge = decision.get("edge", "unknown")
            signal_confidence = decision.get("confidence", 0.0)
        
        # Build the packet
        packet = {
            # OHLC data (chart bar)
            "time": time_str,
            "open": candle.get("open"),
            "high": candle.get("high"),
            "low": candle.get("low"),
            "close": candle["close"],
            "volume": candle.get("volume"),
            
            # Signal data (what to draw)
            "signal": signal,
            "edge": signal_edge,
            "confidence": signal_confidence,
            
            # Context data (annotations)
            "session": context.get("session"),
            "killzone": context.get("killzone", False),
            "news_active": context.get("news", {}).get("active", False),
            "iceberg_score": context.get("iceberg_score", 0.0),
            
            # Explanation (tooltip text)
            "tooltip": explanation.get("summary") if explanation else None,
        }
        
        return packet
    
    def record(self, candle, context, decision, explanation=None):
        """
        Build and store packet.
        
        Args:
            Same as build()
        
        Returns:
            The packet that was stored
        """
        packet = self.build(candle, context, decision, explanation)
        self.packets.append(packet)
        return packet
    
    def export(self):
        """Return all packets as list."""
        return self.packets
    
    def export_json(self, filepath):
        """Save all packets to JSON file."""
        import json
        with open(filepath, "w") as f:
            json.dump(self.packets, f, indent=2)
        return filepath
    
    def get_signals(self):
        """Get only packets with signals (buys/sells)."""
        return [p for p in self.packets if p["signal"] is not None]
    
    def get_by_session(self, session_name):
        """Get all packets from specific session."""
        return [p for p in self.packets if p["session"] == session_name]
    
    def get_high_confidence(self, min_confidence=0.70):
        """Get packets with confidence above threshold."""
        return [
            p for p in self.packets 
            if p["confidence"] >= min_confidence
        ]
    
    def get_killzone_packets(self):
        """Get packets marked as killzone."""
        return [p for p in self.packets if p["killzone"]]
    
    def get_news_packets(self):
        """Get packets with active news."""
        return [p for p in self.packets if p["news_active"]]
    
    def length(self):
        """Number of packets recorded."""
        return len(self.packets)
    
    def signal_count(self):
        """Number of signal packets (trades)."""
        return len(self.get_signals())
