"""
STEP 23: Trade Outcome Analyzer
Measures EDGE, not profit
Reaction quality, timing accuracy, false signal rate
"""


class TradeOutcomeAnalyzer:
    """
    After AI generates a signal, measure what happened next.
    NOT how much money was made.
    Whether the setup worked as expected.
    """

    def evaluate_signal(self, snapshot, future_candles, max_lookahead=30):
        """
        Evaluate signal quality based on what happened next.

        Args:
            snapshot: AI snapshot with decision
            future_candles: list of next N candles
            max_lookahead: how far ahead to measure (default 30 bars = 30 min)

        Returns:
            {
                "signal_action": BUY/SELL,
                "entry_price": price at signal,
                "reaction": pips in intended direction,
                "heat": pips of opposing pressure,
                "timing_bars": bars until reversal started,
                "was_trapped": bool,
                "max_favorable": best move in direction,
                "max_adverse": worst move against direction,
            }
        """
        if not snapshot["decision"] or snapshot["decision"].get("action") == "WAIT":
            return None

        entry = snapshot["price"]
        direction = snapshot["decision"]["action"]

        if len(future_candles) < 1:
            return None

        # Measure price action in next N bars
        future_slice = future_candles[:max_lookahead]
        high = max(c["high"] for c in future_slice)
        low = min(c["low"] for c in future_slice)

        # Calculate reaction (move in intended direction)
        # vs heat (move against intended direction)
        if direction == "SELL":
            reaction = entry - low  # Downside favorable
            heat = high - entry  # Upside heat (trapped)
            is_favorable_direction = low < entry

        elif direction == "BUY":
            reaction = high - entry  # Upside favorable
            heat = entry - low  # Downside heat (trapped)
            is_favorable_direction = high > entry

        else:
            return None

        # Find when reversal started (heat peak)
        timing_bars = self._find_reversal_bar(
            future_slice, direction
        )

        return {
            "signal_action": direction,
            "entry_price": entry,
            "reaction_pips": round(reaction, 2),
            "heat_pips": round(heat, 2),
            "timing_bars": timing_bars,
            "was_trapped": heat > reaction,
            "max_favorable": round(reaction, 2),
            "max_adverse": round(heat, 2),
            "signal_worked": is_favorable_direction,
        }

    def _find_reversal_bar(self, candles, direction):
        """Find bar number where price reversed against signal"""
        if direction == "BUY":
            # Looking for a lower low that suggests rejection
            peak = candles[0]["high"]
            for i, c in enumerate(candles):
                if c["low"] < peak * 0.99:  # 1% pullback
                    return i
        else:
            # Looking for a higher high that suggests rejection
            trough = candles[0]["low"]
            for i, c in enumerate(candles):
                if c["high"] > trough * 1.01:  # 1% pullback
                    return i

        return len(candles)  # No reversal found

    def evaluate_batch(self, snapshots_with_outcomes):
        """
        Analyze a batch of signals.

        Args:
            snapshots_with_outcomes: list of {snapshot, outcome} dicts

        Returns:
            aggregated metrics
        """
        outcomes = [
            s["outcome"]
            for s in snapshots_with_outcomes
            if s.get("outcome")
        ]

        if not outcomes:
            return {}

        reactions = [o["reaction_pips"] for o in outcomes]
        heat = [o["heat_pips"] for o in outcomes]
        timings = [o["timing_bars"] for o in outcomes]

        return {
            "total_signals": len(outcomes),
            "avg_reaction": round(sum(reactions) / len(reactions), 2),
            "avg_heat": round(sum(heat) / len(heat), 2),
            "max_heat": round(max(heat), 2),
            "avg_timing_bars": round(
                sum(timings) / len(timings), 1
            ),
            "signals_worked": sum(
                1 for o in outcomes if o["signal_worked"]
            ),
            "success_rate": round(
                sum(1 for o in outcomes if o["signal_worked"])
                / len(outcomes),
                2,
            ),
            "avg_reaction_to_heat_ratio": round(
                sum(reactions) / sum(heat) if sum(heat) > 0 else 0, 2
            ),
        }
