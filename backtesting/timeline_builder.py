# backtesting/timeline_builder.py
"""
TimelineBuilder: Complete decision history for institutional audit trail.

Stores candle-by-candle reasoning so you can:
- Scrub through any trading day
- Understand why AI skipped trades
- See confidence evolution
- Audit signal quality retrospectively
"""

from datetime import datetime
import json


class TimelineBuilder:
    """Records every candle's decision context and reasoning."""
    
    def __init__(self):
        """Initialize empty timeline."""
        self.timeline = []
        self.metadata = {
            "start_time": None,
            "end_time": None,
            "total_candles": 0,
            "total_trades": 0,
            "skipped_trades": 0,
        }
    
    def record(self, candle, context, decision, explanation):
        """
        Add single candle to timeline.
        
        Args:
            candle: Dict with time, open, high, low, close
            context: Dict with session, killzone, news, iceberg_score, confidence
            decision: Dict with action/edge/confidence, or None
            explanation: Dict with summary and details from ExplanationEngine
        """
        entry = {
            "time": candle["time"].isoformat() if hasattr(candle["time"], "isoformat") else str(candle["time"]),
            "price": {
                "open": candle.get("open"),
                "high": candle.get("high"),
                "low": candle.get("low"),
                "close": candle["close"],
            },
            "session": context.get("session"),
            "killzone": context.get("killzone", False),
            "news": {
                "active": context.get("news", {}).get("active", False),
                "name": context.get("news", {}).get("name"),
                "impact": context.get("news", {}).get("impact"),
            },
            "iceberg_score": context.get("iceberg_score", 0.0),
            "confidence": context.get("confidence", 0.0),
            "decision": {
                "action": decision.get("action") if decision else None,
                "edge": decision.get("edge") if decision else None,
                "confidence": decision.get("confidence") if decision else 0.0,
                "is_trade": decision is not None,
            },
            "explanation": explanation.get("summary") if explanation else "No explanation",
            "details": explanation.get("details") if explanation else [],
        }
        
        self.timeline.append(entry)
        
        # Update metadata
        if not self.metadata["start_time"]:
            self.metadata["start_time"] = entry["time"]
        self.metadata["end_time"] = entry["time"]
        self.metadata["total_candles"] += 1
        if decision:
            self.metadata["total_trades"] += 1
        else:
            self.metadata["skipped_trades"] += 1
    
    def export(self):
        """Export full timeline as list of dicts."""
        return self.timeline
    
    def export_json(self, filepath):
        """Save timeline to JSON file."""
        output = {
            "metadata": self.metadata,
            "timeline": self.timeline,
        }
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)
        return filepath
    
    def export_csv(self, filepath):
        """Save timeline to CSV file (simplified)."""
        import csv
        
        if not self.timeline:
            return filepath
        
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "time",
                    "price",
                    "session",
                    "killzone",
                    "news_active",
                    "iceberg_score",
                    "confidence",
                    "decision",
                    "explanation",
                ],
            )
            writer.writeheader()
            for entry in self.timeline:
                writer.writerow({
                    "time": entry["time"],
                    "price": entry["price"]["close"],
                    "session": entry["session"],
                    "killzone": entry["killzone"],
                    "news_active": entry["news"]["active"],
                    "iceberg_score": entry["iceberg_score"],
                    "confidence": entry["confidence"],
                    "decision": entry["decision"]["action"] or "SKIP",
                    "explanation": entry["explanation"],
                })
        return filepath
    
    def get_trades_only(self):
        """Filter timeline to only trades (decisions != None)."""
        return [e for e in self.timeline if e["decision"]["is_trade"]]
    
    def get_skipped_only(self):
        """Filter timeline to only skipped candles."""
        return [e for e in self.timeline if not e["decision"]["is_trade"]]
    
    def get_session_trades(self, session_name):
        """Get all trades in specific session (ASIA, LONDON, NEW_YORK, OFF_SESSION)."""
        return [
            e for e in self.timeline 
            if e["session"] == session_name and e["decision"]["is_trade"]
        ]
    
    def get_summary(self):
        """Return metadata summary."""
        return {
            "start_time": self.metadata["start_time"],
            "end_time": self.metadata["end_time"],
            "total_candles": self.metadata["total_candles"],
            "total_trades": self.metadata["total_trades"],
            "skipped_trades": self.metadata["skipped_trades"],
            "trade_ratio": (
                self.metadata["total_trades"] / self.metadata["total_candles"]
                if self.metadata["total_candles"] > 0
                else 0.0
            ),
        }
    
    def get_by_time(self, timestamp):
        """Get single timeline entry by timestamp."""
        for entry in self.timeline:
            if entry["time"] == timestamp:
                return entry
        return None
    
    def length(self):
        """Return number of candles recorded."""
        return len(self.timeline)
