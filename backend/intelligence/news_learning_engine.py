"""
STEP 22: News Impact Learning Engine
Learns how different news types behave (CPI, NFP, FOMC)
and adapts confidence based on post-news reaction patterns
"""

from typing import Dict, List
from datetime import datetime, timedelta
from enum import Enum


class NewsType(Enum):
    """High-impact economic news types"""
    CPI = "CPI"
    NFP = "NFP"
    FOMC = "FOMC"
    PMI = "PMI"
    GDP = "GDP"
    BOE = "BOE"
    ECB = "ECB"
    PPI = "PPI"
    RETAIL = "RETAIL"
    EMPLOYMENT = "EMPLOYMENT"


class NewsReactionType(Enum):
    """How price reacted to news"""
    CONTINUATION = "continuation"  # Trend continued after spike
    REVERSAL = "reversal"  # Price reversed after initial spike
    TRAP = "trap"  # False break then reversal
    CHOP = "chop"  # Ranges, no direction
    EXPANSION = "expansion"  # Large expansion then consolidation
    NEUTRAL = "neutral"  # No notable reaction


class NewsImpactLearningEngine:
    """
    Learns historical patterns for news events.
    After 5-10 events per type, OIS knows:
    - How far price typically moves
    - Whether it continues or reverses
    - Optimal time to trade post-news
    """

    def __init__(self):
        self.news_memory: Dict[str, Dict] = {}

        # Initialize tracking for each news type
        for news_type in NewsType:
            self.news_memory[news_type.value] = {
                "total_events": 0,
                "reactions": {
                    "continuation": 0,
                    "reversal": 0,
                    "trap": 0,
                    "chop": 0,
                    "expansion": 0,
                    "neutral": 0,
                },
                "avg_initial_range": 0,  # Pips in first 5 minutes
                "avg_total_range": 0,  # Total pips before stabilization
                "avg_time_to_reversal": 0,  # If it reverses, how long
                "events": [],  # Historical records
                "confidence_adjustment": 0.0,  # What to adjust by
            }

        # Timings (minutes post-news)
        self.consolidation_windows = {
            "CPI": (15, 60),  # Typically settles in 15-60 min
            "NFP": (20, 120),  # Longer consolidation
            "FOMC": (30, 180),  # Very long consolidation
        }

    def record_news_event(
        self,
        news_type: str,
        reaction: str,
        initial_range_pips: float,
        total_range_pips: float,
        time_to_reversal_minutes: float = 0,
        direction: str = "UP",
        impact_level: str = "HIGH",
    ):
        """Record a news event and its price reaction"""
        if news_type not in self.news_memory:
            return

        memory = self.news_memory[news_type]

        # Record event
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "reaction": reaction,
            "initial_range": initial_range_pips,
            "total_range": total_range_pips,
            "time_to_reversal": time_to_reversal_minutes,
            "direction": direction,
            "impact_level": impact_level,
        }
        memory["events"].append(event)

        # Keep last 20 events
        if len(memory["events"]) > 20:
            memory["events"].pop(0)

        # Update reaction count
        memory["total_events"] += 1
        if reaction in memory["reactions"]:
            memory["reactions"][reaction] += 1

        # Update averages
        self._update_averages(news_type)
        self._calculate_confidence_adjustment(news_type)

    def _update_averages(self, news_type: str):
        """Recalculate average metrics for a news type"""
        memory = self.news_memory[news_type]
        events = memory["events"]

        if not events:
            return

        memory["avg_initial_range"] = sum(e["initial_range"] for e in events) / len(events)
        memory["avg_total_range"] = sum(e["total_range"] for e in events) / len(events)

        reversals = [e for e in events if e["reaction"] == "reversal"]
        if reversals:
            memory["avg_time_to_reversal"] = sum(
                e["time_to_reversal"] for e in reversals
            ) / len(reversals)
        else:
            memory["avg_time_to_reversal"] = 0

    def _calculate_confidence_adjustment(self, news_type: str):
        """
        Calculate how to adjust confidence when trading post-news.
        Positive = increase confidence in continuation setups
        Negative = decrease confidence (too chaotic)
        """
        memory = self.news_memory[news_type]

        if memory["total_events"] < 3:
            memory["confidence_adjustment"] = 0.0
            return

        reactions = memory["reactions"]
        total = sum(reactions.values())

        continuation_rate = reactions.get("continuation", 0) / total
        reversal_rate = reactions.get("reversal", 0) / total
        chop_rate = reactions.get("chop", 0) / total

        # Logic:
        # - If mostly continuation (>60%) = boost confidence in trend setups
        # - If mostly reversal (>50%) = reduce confidence (too choppy)
        # - If lots of chop (>40%) = significantly reduce confidence

        if chop_rate > 0.40:
            memory["confidence_adjustment"] = -0.15  # Very unreliable
        elif reversal_rate > 0.50:
            memory["confidence_adjustment"] = -0.10  # Choppy
        elif continuation_rate > 0.60:
            memory["confidence_adjustment"] = 0.10  # Reliable trend continuation
        else:
            memory["confidence_adjustment"] = 0.0

    def get_confidence_adjustment(self, news_type: str, minutes_post_news: float = 0) -> float:
        """
        Get confidence adjustment for trading post-news.
        Larger adjustment window = larger effect (fade away after consolidation).
        """
        if news_type not in self.news_memory:
            return 0.0

        base_adjustment = self.news_memory[news_type]["confidence_adjustment"]

        # Fade adjustment over time
        # Full effect up to 50% of consolidation window
        # Then linear fade to zero
        consolidation = self.consolidation_windows.get(news_type, (30, 120))
        max_window = consolidation[1]
        full_effect_window = max_window * 0.5

        if minutes_post_news < full_effect_window:
            return base_adjustment
        elif minutes_post_news > max_window:
            return 0.0
        else:
            # Linear fade
            remaining = max_window - minutes_post_news
            fade_rate = remaining / (max_window - full_effect_window)
            return base_adjustment * fade_rate

    def get_news_stats(self, news_type: str = None) -> Dict:
        """Get detailed stats for a news type"""
        if news_type and news_type in self.news_memory:
            memory = self.news_memory[news_type]
            return {
                "news_type": news_type,
                "total_events": memory["total_events"],
                "reactions": memory["reactions"],
                "avg_initial_range": memory["avg_initial_range"],
                "avg_total_range": memory["avg_total_range"],
                "avg_time_to_reversal": memory["avg_time_to_reversal"],
                "confidence_adjustment": memory["confidence_adjustment"],
                "recent_events": memory["events"][-5:],
            }

        # Return all stats
        return {
            news: self.get_news_stats(news) for news in self.news_memory.keys()
        }

    def get_most_reliable_news(self) -> List[str]:
        """Get news types with positive confidence adjustment (>0.08)"""
        reliable = []
        for news_type, memory in self.news_memory.items():
            if memory["total_events"] >= 3 and memory["confidence_adjustment"] > 0.08:
                reliable.append(news_type)
        return sorted(reliable, key=lambda x: self.news_memory[x]["confidence_adjustment"], reverse=True)

    def get_unreliable_news(self) -> List[str]:
        """Get news types with negative confidence adjustment (<-0.08)"""
        unreliable = []
        for news_type, memory in self.news_memory.items():
            if memory["total_events"] >= 3 and memory["confidence_adjustment"] < -0.08:
                unreliable.append(news_type)
        return sorted(unreliable, key=lambda x: self.news_memory[x]["confidence_adjustment"])

    def export_state(self) -> Dict:
        """Export for persistence"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "news_memory": self.news_memory,
        }

    def import_state(self, state: Dict):
        """Import from file"""
        if "news_memory" in state:
            self.news_memory = state["news_memory"]

    def reset_news_type(self, news_type: str):
        """Reset learning for a news type"""
        if news_type in self.news_memory:
            self.news_memory[news_type] = {
                "total_events": 0,
                "reactions": {
                    "continuation": 0,
                    "reversal": 0,
                    "trap": 0,
                    "chop": 0,
                    "expansion": 0,
                    "neutral": 0,
                },
                "avg_initial_range": 0,
                "avg_total_range": 0,
                "avg_time_to_reversal": 0,
                "events": [],
                "confidence_adjustment": 0.0,
            }
