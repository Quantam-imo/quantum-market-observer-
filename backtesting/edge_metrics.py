"""
STEP 23: Edge Metrics
Institutional-grade quality metrics
Timing accuracy, liquidity respect, false signal rate
"""


class EdgeMetrics:
    """
    Evaluate system quality on professional metrics.
    NOT profit curves.
    Timing precision. Edge clarity. Risk management.
    """

    def __init__(self):
        self.outcomes = []
        self.snapshots = []

    def record(self, snapshot, outcome):
        """Record a signal + its outcome"""
        self.snapshots.append(snapshot)
        self.outcomes.append(outcome)

    def timing_accuracy(self):
        """
        Did reversal happen within expected bars?
        Professional metric: consistency of reaction timing
        """
        if not self.outcomes:
            return None

        timings = [o["timing_bars"] for o in self.outcomes if o]
        if not timings:
            return None

        return {
            "avg_bars_to_reaction": round(sum(timings) / len(timings), 1),
            "median_bars": sorted(timings)[len(timings) // 2],
            "fast_reactions": sum(1 for t in timings if t <= 5),
            "slow_reactions": sum(1 for t in timings if t > 15),
            "consistency": "GOOD"
            if len(set(timings)) < len(timings) / 3
            else "VARIABLE",
        }

    def liquidity_respect(self):
        """
        Did price react at liquidity zones?
        Did iceberg absorption match?
        """
        outcomes_with_reaction = [
            o for o in self.outcomes if o and o.get("signal_worked")
        ]
        if not self.outcomes:
            return None

        success_rate = (
            len(outcomes_with_reaction) / len(self.outcomes)
        )
        return {
            "signals_with_favorable_reaction": len(outcomes_with_reaction),
            "liquidity_respect_rate": round(success_rate, 2),
            "trapped_signals": sum(
                1 for o in self.outcomes if o and o.get("was_trapped")
            ),
            "trap_rate": round(
                sum(1 for o in self.outcomes if o and o.get("was_trapped"))
                / len(self.outcomes),
                2,
            ),
        }

    def false_signal_rate(self):
        """
        How often confidence >= 70% but signal failed?
        Professional risk metric
        """
        high_confidence = [
            s for s in self.snapshots
            if s.get("decision", {}).get("confidence", 0) >= 0.70
        ]
        if not high_confidence:
            return None

        # Match with outcomes
        failed_high_confidence = 0
        for s, o in zip(self.snapshots, self.outcomes):
            if (
                s.get("decision", {}).get("confidence", 0) >= 0.70
                and o
                and not o.get("signal_worked")
            ):
                failed_high_confidence += 1

        return {
            "high_confidence_signals": len(high_confidence),
            "high_conf_failed": failed_high_confidence,
            "false_signal_rate": round(
                failed_high_confidence / len(high_confidence)
                if high_confidence
                else 0,
                2,
            ),
        }

    def max_heat_analysis(self):
        """
        Worst drawdown before target?
        Maximum adverse excursion metric
        """
        if not self.outcomes:
            return None

        heats = [o["heat_pips"] for o in self.outcomes if o]
        if not heats:
            return None

        return {
            "max_heat": round(max(heats), 2),
            "avg_heat": round(sum(heats) / len(heats), 2),
            "signals_with_heat_gt_10": sum(
                1 for h in heats if h > 10
            ),
            "max_heat_rate": round(max(heats) / 10, 2),  # In 10-pip units
        }

    def hold_quality(self):
        """
        How clean was the move?
        Reaction vs heat ratio (R/R-like metric)
        """
        if not self.outcomes:
            return None

        outcomes_valid = [o for o in self.outcomes if o]
        if not outcomes_valid:
            return None

        ratios = [
            o["reaction_pips"] / (o["heat_pips"] + 0.1)
            for o in outcomes_valid
        ]

        return {
            "avg_reaction_to_heat_ratio": round(
                sum(ratios) / len(ratios), 2
            ),
            "clean_holds": sum(
                1 for r in ratios if r >= 2.0
            ),  # 2:1 or better
            "clean_hold_rate": round(
                sum(1 for r in ratios if r >= 2.0) / len(ratios), 2
            ),
        }

    def edge_decay_check(self, session_data=None):
        """
        Did performance degrade in chop?
        Session-specific quality tracking
        """
        if not self.outcomes:
            return None

        if not session_data:
            # Simple time-based decay check
            first_half = self.outcomes[: len(self.outcomes) // 2]
            second_half = self.outcomes[len(self.outcomes) // 2 :]

            first_success = sum(
                1 for o in first_half if o and o.get("signal_worked")
            )
            second_success = sum(
                1 for o in second_half if o and o.get("signal_worked")
            )

            return {
                "first_half_success_rate": round(
                    first_success / len(first_half)
                    if first_half
                    else 0,
                    2,
                ),
                "second_half_success_rate": round(
                    second_success / len(second_half)
                    if second_half
                    else 0,
                    2,
                ),
                "decay_detected": first_success > second_success * 1.2,
            }

        return None

    def summary(self):
        """Generate complete professional summary"""
        return {
            "timing": self.timing_accuracy(),
            "liquidity": self.liquidity_respect(),
            "false_signals": self.false_signal_rate(),
            "heat": self.max_heat_analysis(),
            "hold_quality": self.hold_quality(),
            "decay": self.edge_decay_check(),
            "total_snapshots": len(self.snapshots),
            "total_outcomes": len(
                [o for o in self.outcomes if o]
            ),
        }
