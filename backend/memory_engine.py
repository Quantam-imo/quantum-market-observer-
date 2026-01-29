import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class MemoryEngine:
    def __init__(self, memory_file="trade_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory = self._load_memory()
        
    def _load_memory(self):
        """Load historical trade data"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "trades": [],
            "icebergs": [],
            "patterns": {},
            "stats": {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0.0
            }
        }
    
    def _save_memory(self):
        """Persist memory to disk"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def record_trade(self, trade: Dict):
        """Record a completed trade"""
        trade["timestamp"] = datetime.now().isoformat()
        self.memory["trades"].append(trade)
        
        # Update stats
        self.memory["stats"]["total_trades"] += 1
        if trade.get("pnl", 0) > 0:
            self.memory["stats"]["winning_trades"] += 1
        else:
            self.memory["stats"]["losing_trades"] += 1
        self.memory["stats"]["total_pnl"] += trade.get("pnl", 0)
        
        self._save_memory()
    
    def record_iceberg(self, iceberg: Dict):
        """Record an iceberg zone interaction"""
        iceberg["timestamp"] = datetime.now().isoformat()
        self.memory["icebergs"].append(iceberg)
        self._save_memory()

    def iceberg_success_rate(self, zone_price: float, tolerance=10.0):
        """Calculate success rate for a specific iceberg zone"""
        relevant = [
            i for i in self.memory["icebergs"] 
            if abs(i.get("price", 0) - zone_price) < tolerance
        ]
        if not relevant:
            return 0.5
        
        wins = [i for i in relevant if i.get("result") == "WIN"]
        return len(wins) / len(relevant)
    
    def get_pattern_success_rate(self, pattern_name: str):
        """Get historical success rate for a specific pattern"""
        if pattern_name in self.memory["patterns"]:
            p = self.memory["patterns"][pattern_name]
            total = p["wins"] + p["losses"]
            return p["wins"] / total if total > 0 else 0.5
        return 0.5
    
    def record_pattern_outcome(self, pattern_name: str, success: bool):
        """Record outcome of trading a specific pattern"""
        if pattern_name not in self.memory["patterns"]:
            self.memory["patterns"][pattern_name] = {"wins": 0, "losses": 0}
        
        if success:
            self.memory["patterns"][pattern_name]["wins"] += 1
        else:
            self.memory["patterns"][pattern_name]["losses"] += 1
        
        self._save_memory()
    
    def get_recent_trades(self, limit=10) -> List[Dict]:
        """Get most recent trades"""
        return self.memory["trades"][-limit:]
    
    def get_stats(self) -> Dict:
        """Get overall trading statistics"""
        stats = self.memory["stats"].copy()
        if stats["total_trades"] > 0:
            stats["win_rate"] = stats["winning_trades"] / stats["total_trades"]
            stats["avg_pnl"] = stats["total_pnl"] / stats["total_trades"]
        return stats
