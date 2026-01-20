"""
STEP 22: Edge Decay Engine
Detects when trading setups stop working and automatically reduces confidence
"""

from typing import Dict, List
from datetime import datetime, timedelta


class EdgeDecayEngine:
    """
    Monitors edge performance and detects decay.
    When a setup that worked 70%+ drops below 55%, flags it as decaying.
    """

    def __init__(self):
        self.edge_performance: Dict[str, Dict] = {
            "iceberg": {
                "wins": 0,
                "losses": 0,
                "recent_results": [],  # Last 20 trades
                "decay_flag": False,
                "confidence_penalty": 0.0,
            },
            "gann_breakout": {
                "wins": 0,
                "losses": 0,
                "recent_results": [],
                "decay_flag": False,
                "confidence_penalty": 0.0,
            },
            "astro_aspect": {
                "wins": 0,
                "losses": 0,
                "recent_results": [],
                "decay_flag": False,
                "confidence_penalty": 0.0,
            },
            "cycle_inflection": {
                "wins": 0,
                "losses": 0,
                "recent_results": [],
                "decay_flag": False,
                "confidence_penalty": 0.0,
            },
            "liquidity_sweep": {
                "wins": 0,
                "losses": 0,
                "recent_results": [],
                "decay_flag": False,
                "confidence_penalty": 0.0,
            },
        }

        # Threshold tuning
        self.min_samples = 20  # Need at least 20 trades before detecting decay
        self.initial_edge_threshold = 0.70  # 70% win rate establishes edge
        self.decay_threshold = 0.55  # Below 55% = decay detected
        self.decay_penalty = 0.10  # Reduce confidence by 10% per decay
        self.max_penalty = 0.30  # Never go below 30% confidence

    def record_result(self, edge_name: str, win: bool, context: Dict = None):
        """Record trade result for an edge"""
        if edge_name not in self.edge_performance:
            return

        edge = self.edge_performance[edge_name]

        if win:
            edge["wins"] += 1
        else:
            edge["losses"] += 1

        # Store recent result (last 20 only)
        edge["recent_results"].append(
            {"win": win, "timestamp": datetime.utcnow(), "context": context or {}}
        )
        if len(edge["recent_results"]) > 20:
            edge["recent_results"].pop(0)

        # Re-evaluate decay
        self._evaluate_decay(edge_name)

    def _evaluate_decay(self, edge_name: str):
        """Check if edge is showing decay"""
        edge = self.edge_performance[edge_name]
        total = edge["wins"] + edge["losses"]

        # Need minimum samples
        if total < self.min_samples:
            edge["decay_flag"] = False
            return

        # Calculate win rate
        win_rate = edge["wins"] / total if total > 0 else 0.0

        # Decay detection logic
        if win_rate < self.decay_threshold:
            # Edge is decaying
            edge["decay_flag"] = True
            # Calculate confidence penalty
            decay_magnitude = (self.initial_edge_threshold - win_rate) / self.initial_edge_threshold
            edge["confidence_penalty"] = min(
                decay_magnitude * self.decay_penalty, self.max_penalty
            )
        else:
            # Edge still performing
            edge["decay_flag"] = False
            edge["confidence_penalty"] = 0.0

    def get_decay_penalty(self, edge_name: str) -> float:
        """Get confidence penalty for an edge (0.0 to 0.30)"""
        if edge_name in self.edge_performance:
            return self.edge_performance[edge_name]["confidence_penalty"]
        return 0.0

    def get_decay_status(self, edge_name: str) -> Dict:
        """Get full decay status for an edge"""
        if edge_name not in self.edge_performance:
            return {}

        edge = self.edge_performance[edge_name]
        total = edge["wins"] + edge["losses"]
        win_rate = edge["wins"] / total if total > 0 else 0.0

        return {
            "edge": edge_name,
            "total_trades": total,
            "win_rate": win_rate,
            "is_decaying": edge["decay_flag"],
            "confidence_penalty": edge["confidence_penalty"],
            "wins": edge["wins"],
            "losses": edge["losses"],
        }

    def get_all_decays(self) -> List[Dict]:
        """Get status of all edges"""
        return [self.get_decay_status(edge) for edge in self.edge_performance.keys()]

    def reset_edge(self, edge_name: str):
        """Reset statistics for an edge (e.g., regime change)"""
        if edge_name in self.edge_performance:
            self.edge_performance[edge_name] = {
                "wins": 0,
                "losses": 0,
                "recent_results": [],
                "decay_flag": False,
                "confidence_penalty": 0.0,
            }

    def get_strongest_edges(self, limit: int = 3) -> List[str]:
        """Get edges that are currently performing best"""
        edges = self.get_all_decays()
        # Filter to only tested edges
        tested = [e for e in edges if e["total_trades"] >= 10]
        # Sort by win rate descending
        sorted_edges = sorted(tested, key=lambda x: x["win_rate"], reverse=True)
        return [e["edge"] for e in sorted_edges[:limit]]

    def get_weakest_edges(self, limit: int = 3) -> List[str]:
        """Get edges that need attention"""
        edges = self.get_all_decays()
        # Filter to only tested edges
        tested = [e for e in edges if e["total_trades"] >= 10]
        # Sort by win rate ascending
        sorted_edges = sorted(tested, key=lambda x: x["win_rate"])
        decaying = [e for e in sorted_edges if e["is_decaying"]]
        return [e["edge"] for e in decaying[:limit]]

    def export_state(self) -> Dict:
        """Export current edge decay state for persistence"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "edges": self.edge_performance,
        }

    def import_state(self, state: Dict):
        """Import edge decay state from file"""
        if "edges" in state:
            self.edge_performance = state["edges"]
