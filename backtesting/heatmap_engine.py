# backtesting/heatmap_engine.py
"""
HeatmapEngine: Generate confidence and activity heatmaps.

Produces visual-ready data for:
- Confidence heatmap (dark=high, light=low)
- Activity heatmap (where signals were generated)
- Session heatmap (performance by session)
- Risk heatmap (drawdown visualization)

UI-agnostic but UI-ready (JSON serializable).
"""


class HeatmapEngine:
    """Generate heatmaps from timeline data."""
    
    def __init__(self):
        """Initialize heatmap engine."""
        self.heatmaps = {}
    
    def generate_confidence_heatmap(self, timeline):
        """
        Generate confidence heatmap (time series of confidence levels).
        
        Args:
            timeline: List of timeline entries from TimelineBuilder
        
        Returns:
            List of dicts with time and confidence_level
        """
        heatmap = []
        
        for item in timeline:
            time = item.get("time")
            confidence = item.get("confidence", 0.0)
            
            # Categorize confidence level
            if confidence >= 0.85:
                level = "VERY_HIGH"
            elif confidence >= 0.75:
                level = "HIGH"
            elif confidence >= 0.65:
                level = "MEDIUM"
            elif confidence >= 0.50:
                level = "LOW"
            else:
                level = "VERY_LOW"
            
            heatmap.append({
                "time": time,
                "confidence": confidence,
                "level": level,
            })
        
        self.heatmaps["confidence"] = heatmap
        return heatmap
    
    def generate_activity_heatmap(self, timeline):
        """
        Generate activity heatmap (when signals were generated).
        
        Args:
            timeline: List of timeline entries
        
        Returns:
            List of dicts with time and activity info
        """
        heatmap = []
        
        for item in timeline:
            time = item.get("time")
            decision = item.get("decision", {})
            is_trade = decision.get("is_trade", False)
            action = decision.get("action")
            
            activity = {
                "time": time,
                "active": is_trade,
                "signal": action if is_trade else None,
                "confidence": item.get("confidence", 0.0),
            }
            
            heatmap.append(activity)
        
        self.heatmaps["activity"] = heatmap
        return heatmap
    
    def generate_session_heatmap(self, timeline):
        """
        Generate session-based heatmap.
        
        Args:
            timeline: List of timeline entries
        
        Returns:
            Dict with session statistics
        """
        sessions = {}
        
        for item in timeline:
            session = item.get("session", "UNKNOWN")
            is_trade = item.get("decision", {}).get("is_trade", False)
            confidence = item.get("confidence", 0.0)
            
            if session not in sessions:
                sessions[session] = {
                    "count": 0,
                    "trades": 0,
                    "avg_confidence": 0.0,
                    "high_confidence_trades": 0,
                }
            
            sessions[session]["count"] += 1
            if is_trade:
                sessions[session]["trades"] += 1
            
            # Update running average
            prev_avg = sessions[session]["avg_confidence"]
            sessions[session]["avg_confidence"] = (
                (prev_avg * (sessions[session]["count"] - 1) + confidence) / 
                sessions[session]["count"]
            )
            
            if is_trade and confidence >= 0.75:
                sessions[session]["high_confidence_trades"] += 1
        
        # Add trade ratios
        for session in sessions:
            count = sessions[session]["count"]
            sessions[session]["trade_ratio"] = (
                sessions[session]["trades"] / count if count > 0 else 0
            )
        
        self.heatmaps["session"] = sessions
        return sessions
    
    def generate_killzone_heatmap(self, timeline):
        """
        Generate killzone heatmap (risky periods).
        
        Args:
            timeline: List of timeline entries
        
        Returns:
            List of dicts marking killzone periods
        """
        heatmap = []
        
        for item in timeline:
            time = item.get("time")
            killzone = item.get("killzone", False)
            is_trade = item.get("decision", {}).get("is_trade", False)
            
            entry = {
                "time": time,
                "in_killzone": killzone,
                "traded_in_killzone": killzone and is_trade,
                "confidence": item.get("confidence", 0.0),
            }
            
            heatmap.append(entry)
        
        self.heatmaps["killzone"] = heatmap
        return heatmap
    
    def generate_news_impact_heatmap(self, timeline):
        """
        Generate news impact heatmap.
        
        Args:
            timeline: List of timeline entries
        
        Returns:
            List of dicts showing news proximity and trade decisions
        """
        heatmap = []
        
        for item in timeline:
            time = item.get("time")
            news = item.get("news", {})
            is_trade = item.get("decision", {}).get("is_trade", False)
            
            entry = {
                "time": time,
                "news_active": news.get("active", False),
                "news_impact": news.get("impact"),
                "traded_near_news": news.get("active", False) and is_trade,
                "confidence": item.get("confidence", 0.0),
            }
            
            heatmap.append(entry)
        
        self.heatmaps["news"] = heatmap
        return heatmap
    
    def generate_iceberg_heatmap(self, timeline):
        """
        Generate iceberg persistence heatmap.
        
        Args:
            timeline: List of timeline entries
        
        Returns:
            List of dicts with iceberg scores
        """
        heatmap = []
        
        for item in timeline:
            time = item.get("time")
            iceberg_score = item.get("iceberg_score", 0.0)
            is_trade = item.get("decision", {}).get("is_trade", False)
            
            # Categorize persistence
            if iceberg_score >= 0.85:
                persistence_type = "ABSORPTION"
            elif iceberg_score >= 0.70:
                persistence_type = "DEFENSE"
            elif iceberg_score >= 0.50:
                persistence_type = "INTEREST"
            else:
                persistence_type = "RANDOM"
            
            entry = {
                "time": time,
                "iceberg_score": iceberg_score,
                "persistence_type": persistence_type,
                "traded": is_trade,
                "confidence": item.get("confidence", 0.0),
            }
            
            heatmap.append(entry)
        
        self.heatmaps["iceberg"] = heatmap
        return heatmap
    
    def generate_all_heatmaps(self, timeline):
        """
        Generate all heatmaps at once.
        
        Args:
            timeline: List of timeline entries
        
        Returns:
            Dict with all heatmap types
        """
        return {
            "confidence": self.generate_confidence_heatmap(timeline),
            "activity": self.generate_activity_heatmap(timeline),
            "session": self.generate_session_heatmap(timeline),
            "killzone": self.generate_killzone_heatmap(timeline),
            "news": self.generate_news_impact_heatmap(timeline),
            "iceberg": self.generate_iceberg_heatmap(timeline),
        }
    
    def get_heatmap(self, heatmap_type):
        """
        Get specific heatmap.
        
        Args:
            heatmap_type: "confidence", "activity", "session", "killzone", "news", or "iceberg"
        
        Returns:
            Heatmap data, or None if not generated
        """
        return self.heatmaps.get(heatmap_type)
    
    def get_all_heatmaps(self):
        """Return all generated heatmaps."""
        return self.heatmaps
    
    def export_heatmaps_json(self, filepath):
        """
        Export all heatmaps to JSON.
        
        Args:
            filepath: Output file path
        
        Returns:
            Filepath
        """
        import json
        with open(filepath, "w") as f:
            json.dump(self.heatmaps, f, indent=2, default=str)
        return filepath
