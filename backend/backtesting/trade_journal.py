"""
Trade Journal - Logs every trade with full context for AI learning
This is how the system improves over time
"""

import json
from datetime import datetime
from pathlib import Path


class TradeJournal:
    """
    Records every trade with complete context.
    Used for AI memory training and edge analysis.
    """
    
    def __init__(self, journal_dir="trading_journal"):
        self.journal_dir = Path(journal_dir)
        self.journal_dir.mkdir(exist_ok=True)
        self.current_session = []
    
    def log_trade(self, trade_data):
        """
        Log a completed trade.
        
        Args:
            trade_data: Dict with all trade info
                - entry_time, exit_time
                - direction, entry_price, exit_price
                - stop_loss, take_profit_1, take_profit_2
                - r_multiple, result (WIN/LOSS/BE)
                - conditions: QMO, IMO, Gann, Astro, Cycle
                - ai_confidence
                - execution_notes
        """
        trade = {
            "timestamp": datetime.now().isoformat(),
            "data": trade_data
        }
        
        self.current_session.append(trade)
        
        # Auto-save daily
        self._save_daily_journal()
    
    def log_signal(self, signal_data):
        """Log a signal that didn't execute (for context)."""
        signal = {
            "type": "SIGNAL",
            "timestamp": datetime.now().isoformat(),
            "data": signal_data
        }
        self.current_session.append(signal)
    
    def _save_daily_journal(self):
        """Save session to daily file."""
        today = datetime.now().date().isoformat()
        filepath = self.journal_dir / f"journal_{today}.json"
        
        with open(filepath, "w") as f:
            json.dump(self.current_session, f, indent=2)
    
    def analyze_session(self):
        """
        Analyze today's session performance.
        """
        if not self.current_session:
            return None
        
        trades = [t for t in self.current_session if t.get("type") != "SIGNAL"]
        
        analysis = {
            "total_trades": len(trades),
            "winning_trades": sum(1 for t in trades if t["data"].get("result") == "WIN"),
            "losing_trades": sum(1 for t in trades if t["data"].get("result") == "LOSS"),
            "breakeven_trades": sum(1 for t in trades if t["data"].get("result") == "BE"),
            "total_r": sum(t["data"].get("r_multiple", 0) for t in trades),
            "avg_confidence": sum(t["data"].get("ai_confidence", 0) for t in trades) / len(trades) if trades else 0
        }
        
        if analysis["total_trades"] > 0:
            analysis["win_rate"] = analysis["winning_trades"] / analysis["total_trades"]
        
        return analysis
    
    def best_setup_from_journal(self):
        """
        Identify best performing setup types.
        """
        setup_performance = {}
        
        for trade in self.current_session:
            if trade.get("type") == "SIGNAL":
                continue
            
            setup = trade["data"].get("setup_type", "UNKNOWN")
            result = trade["data"].get("result", "UNKNOWN")
            
            if setup not in setup_performance:
                setup_performance[setup] = {"wins": 0, "losses": 0, "total_r": 0}
            
            setup_performance[setup]["wins"] += (1 if result == "WIN" else 0)
            setup_performance[setup]["losses"] += (1 if result == "LOSS" else 0)
            setup_performance[setup]["total_r"] += trade["data"].get("r_multiple", 0)
        
        # Sort by edge
        ranked = sorted(
            setup_performance.items(),
            key=lambda x: (x[1]["wins"] / (x[1]["wins"] + x[1]["losses"] + 0.1)) * x[1]["total_r"],
            reverse=True
        )
        
        return ranked
    
    def identify_weaknesses(self):
        """
        Find where you're losing money (brutal honesty).
        """
        weaknesses = {}
        
        for trade in self.current_session:
            if trade.get("type") == "SIGNAL" or trade["data"].get("result") != "LOSS":
                continue
            
            reason = trade["data"].get("failure_reason", "UNKNOWN")
            
            if reason not in weaknesses:
                weaknesses[reason] = 0
            weaknesses[reason] += 1
        
        # Sort by frequency
        return sorted(weaknesses.items(), key=lambda x: x[1], reverse=True)
    
    def calculate_performance_metrics(self):
        """Full performance summary."""
        analysis = self.analyze_session()
        
        if not analysis:
            return None
        
        print(f"\n{'='*70}")
        print("DAILY PERFORMANCE SUMMARY")
        print(f"{'='*70}\n")
        
        print(f"Total Trades:       {analysis['total_trades']}")
        print(f"Wins:               {analysis['winning_trades']}")
        print(f"Losses:             {analysis['losing_trades']}")
        print(f"Breakeven:          {analysis['breakeven_trades']}")
        print(f"Win Rate:           {analysis.get('win_rate', 0):.1%}")
        print(f"Total R:            {analysis['total_r']:.2f}R")
        print(f"Avg Confidence:     {analysis['avg_confidence']:.1%}")
        
        # Best setups
        print(f"\n{'BEST SETUPS':-^70}")
        best = self.best_setup_from_journal()
        for setup, metrics in best[:3]:
            wr = metrics["wins"] / (metrics["wins"] + metrics["losses"] + 0.1)
            print(f"{setup}: {metrics['wins']} wins | "
                  f"WR {wr:.1%} | Total R: {metrics['total_r']:.2f}R")
        
        # Weaknesses
        print(f"\n{'LOSSES & REASONS':-^70}")
        weak = self.identify_weaknesses()
        for reason, count in weak[:3]:
            print(f"{reason}: {count} occurrences")
        
        print(f"\n{'='*70}\n")
        
        return analysis


# Example usage:
if __name__ == "__main__":
    journal = TradeJournal()
    
    # Log a trade
    journal.log_trade({
        "entry_time": "10:35 GMT",
        "exit_time": "11:02 GMT",
        "direction": "SELL",
        "entry_price": 3366,
        "exit_price": 3346,
        "stop_loss": 3374,
        "take_profit_1": 3346,
        "take_profit_2": 3328,
        "r_multiple": 2.8,
        "result": "WIN",
        "setup_type": "NY_PREMIUM_SWEEP",
        "ai_confidence": 0.82,
        "execution_notes": "Clean execution, waited for liquidity"
    })
    
    # Analyze
    journal.calculate_performance_metrics()
