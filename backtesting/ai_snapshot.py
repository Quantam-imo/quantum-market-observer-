"""
STEP 23: AI Snapshot Store
Captures complete AI brain state per candle
This is the gold — allows full debugging and analysis
"""

import json
from datetime import datetime


class AISnapshotStore:
    """
    Stores full AI state for every candle.
    Later: replay visually, debug decisions, learn patterns.
    """

    def __init__(self):
        self.history = []
        self.signal_count = 0
        self.skip_count = 0

    def store(self, candle, context, decision):
        """
        Record complete snapshot of AI state.
        
        Args:
            candle: market data for this bar
            context: AI input (qmo, liquidity, gann, astro, cycle)
            decision: AI verdict (BUY/SELL/WAIT + confidence)
        """
        snapshot = {
            "time": candle["time"],
            "price": candle["close"],
            "qmo": context.get("qmo", {}),
            "liquidity": context.get("liquidity", {}),
            "gann": context.get("gann", {}),
            "astro": context.get("astro", {}),
            "cycle": context.get("cycle", {}),
            "decision": decision or {"action": "WAIT", "confidence": 0.0},
        }

        # Track signals
        if decision and decision.get("action") != "WAIT":
            self.signal_count += 1
        else:
            self.skip_count += 1

        self.history.append(snapshot)

    def all(self):
        """Return all snapshots in order"""
        return self.history

    def signals_only(self):
        """Return only candles where AI generated a signal"""
        return [s for s in self.history if s["decision"]["action"] != "WAIT"]

    def count(self):
        """Return {total_candles, signals, skips}"""
        return {
            "total_candles": len(self.history),
            "signals": self.signal_count,
            "skips": self.skip_count,
            "signal_rate": (
                self.signal_count / len(self.history)
                if len(self.history) > 0
                else 0.0
            ),
        }

    def confidence_distribution(self):
        """Return confidence stats"""
        confidences = [
            s["decision"].get("confidence", 0.0) for s in self.history
        ]
        if not confidences:
            return {}

        return {
            "min": min(confidences),
            "max": max(confidences),
            "avg": sum(confidences) / len(confidences),
            "total_above_70": sum(1 for c in confidences if c >= 0.70),
        }

    def export_json(self, filepath):
        """Export all snapshots to JSON for analysis"""
        with open(filepath, "w") as f:
            json.dump(self.history, f, indent=2, default=str)

    def export_signals_csv(self, filepath):
        """Export signals only to CSV for quick review"""
        import csv

        signals = self.signals_only()
        if not signals:
            return

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "time",
                    "price",
                    "action",
                    "confidence",
                    "qmo_phase",
                    "liquidity_type",
                ],
            )
            writer.writeheader()
            for s in signals:
                writer.writerow(
                    {
                        "time": s["time"],
                        "price": s["price"],
                        "action": s["decision"].get("action", "WAIT"),
                        "confidence": s["decision"].get("confidence", 0.0),
                        "qmo_phase": s["qmo"].get("phase", "unknown"),
                        "liquidity_type": s["liquidity"].get(
                            "type", "unknown"
                        ),
                    }
                )
