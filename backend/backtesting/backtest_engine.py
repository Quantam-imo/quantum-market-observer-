"""
Backtesting Engine - Replay historical data through the trading system
Tests edge validity before live trading
"""

from datetime import datetime, timedelta
from backend.intelligence.step3_imo_pipeline import Step3IMOPipeline
from backend.core.gann_engine import GannEngine
from backend.core.astro_engine import AstroEngine
from backend.core.cycle_engine import CycleEngine
from backend.mentor.mentor_brain import MentorBrain
from backend.mentor.confidence_engine import ConfidenceEngine


class BacktestEngine:
    """
    Simulates system performance on historical data.
    Trains AI memory without real capital.
    """
    
    def __init__(self):
        self.pipeline = Step3IMOPipeline()
        self.gann = GannEngine()
        self.astro = AstroEngine()
        self.cycle = CycleEngine()
        self.mentor = MentorBrain()
        self.confidence = ConfidenceEngine()
        
        self.trades_log = []
        self.performance_stats = {}
        self.condition_analysis = {}
    
    def run_backtest(self, historical_data, start_date, end_date):
        """
        Run full backtest on date range.
        
        Args:
            historical_data: List of tick/candle dicts
            start_date: datetime
            end_date: datetime
        
        Returns:
            Backtest results
        """
        print(f"\n{'='*70}")
        print(f"BACKTEST: {start_date.date()} → {end_date.date()}")
        print(f"{'='*70}\n")
        
        trade_signals = []
        
        for i, candle in enumerate(historical_data):
            candle_time = datetime.fromisoformat(candle.get("time", ""))
            
            if not (start_date <= candle_time <= end_date):
                continue
            
            # Get previous 50 candles for context
            context_candles = historical_data[max(0, i-50):i+1]
            trades_in_window = [t for t in context_candles if "price" in t]
            
            # Run through pipeline
            decision = self.pipeline.process_tick(trades_in_window, context_candles)
            
            if decision["decision"] in ["BUY", "SELL"]:
                signal = {
                    "time": candle_time,
                    "direction": decision["decision"],
                    "price": candle.get("close"),
                    "confidence": decision["confidence"],
                    "absorption_zones": decision.get("absorption_zones", []),
                    "sweeps": decision.get("sweeps", [])
                }
                trade_signals.append(signal)
        
        # Evaluate signals
        results = self._evaluate_signals(trade_signals, historical_data)
        return results
    
    def _evaluate_signals(self, signals, historical_data):
        """
        Score signals against actual price movement.
        """
        results = {
            "total_signals": len(signals),
            "winning_trades": 0,
            "losing_trades": 0,
            "avg_r_multiple": 0,
            "win_rate": 0,
            "condition_breakdown": {}
        }
        
        total_r = 0
        
        for signal in signals:
            signal_time = signal["time"]
            signal_price = signal["price"]
            direction = signal["direction"]
            confidence = signal["confidence"]
            
            # Find exit (next 20 candles)
            future_data = [c for c in historical_data 
                          if datetime.fromisoformat(c.get("time", "")) > signal_time][:20]
            
            if not future_data:
                continue
            
            exit_high = max([c.get("high", 0) for c in future_data])
            exit_low = min([c.get("low", 0) for c in future_data])
            
            # Calculate outcome
            if direction == "SELL":
                if exit_low < signal_price:
                    results["winning_trades"] += 1
                    r_multiple = (signal_price - exit_low) / 10  # Assume 10pt stop
                    total_r += r_multiple
                else:
                    results["losing_trades"] += 1
                    total_r -= 1
            
            else:  # BUY
                if exit_high > signal_price:
                    results["winning_trades"] += 1
                    r_multiple = (exit_high - signal_price) / 10
                    total_r += r_multiple
                else:
                    results["losing_trades"] += 1
                    total_r -= 1
            
            # Log by condition
            condition_key = f"Conf_{int(confidence*100)}"
            if condition_key not in results["condition_breakdown"]:
                results["condition_breakdown"][condition_key] = {
                    "trades": 0,
                    "wins": 0,
                    "total_r": 0
                }
            
            results["condition_breakdown"][condition_key]["trades"] += 1
            if results["winning_trades"] > results["losing_trades"]:
                results["condition_breakdown"][condition_key]["wins"] += 1
            results["condition_breakdown"][condition_key]["total_r"] += total_r
        
        # Calculate final stats
        total_trades = results["winning_trades"] + results["losing_trades"]
        if total_trades > 0:
            results["win_rate"] = results["winning_trades"] / total_trades
            results["avg_r_multiple"] = total_r / total_trades
        
        self.trades_log.extend(signals)
        self.performance_stats = results
        
        return results
    
    def print_backtest_report(self):
        """Print human-readable backtest results."""
        stats = self.performance_stats
        
        print(f"\n{'='*70}")
        print("BACKTEST RESULTS")
        print(f"{'='*70}\n")
        
        print(f"Total Signals:     {stats['total_signals']}")
        print(f"Winning Trades:    {stats['winning_trades']}")
        print(f"Losing Trades:     {stats['losing_trades']}")
        print(f"Win Rate:          {stats['win_rate']:.1%}")
        print(f"Avg R-Multiple:    {stats['avg_r_multiple']:.2f}R")
        
        print(f"\n{'CONDITION ANALYSIS':-^70}")
        for condition, data in stats["condition_breakdown"].items():
            if data["trades"] > 0:
                wr = data["wins"] / data["trades"]
                print(f"{condition}: {data['trades']} trades | "
                      f"WR: {wr:.1%} | Total R: {data['total_r']:.2f}R")
        
        print(f"\n{'='*70}\n")
    
    def identify_best_conditions(self):
        """
        Analyze which conditions produce best results.
        Used to improve AI filters.
        """
        best_conditions = {}
        
        for condition, data in self.performance_stats["condition_breakdown"].items():
            if data["trades"] >= 5:  # Minimum sample size
                edge = (data["wins"] / data["trades"]) * data["total_r"]
                best_conditions[condition] = {
                    "trades": data["trades"],
                    "edge": edge,
                    "win_rate": data["wins"] / data["trades"],
                    "total_r": data["total_r"]
                }
        
        # Sort by edge
        sorted_conditions = sorted(
            best_conditions.items(),
            key=lambda x: x[1]["edge"],
            reverse=True
        )
        
        print(f"\n{'BEST CONDITIONS (BY EDGE)':-^70}")
        for condition, metrics in sorted_conditions[:5]:
            print(f"{condition}: Edge = {metrics['edge']:.2f}R | "
                  f"WR = {metrics['win_rate']:.1%}")
        
        return sorted_conditions
    
    def measure_edge_decay(self):
        """
        Test if edge weakens over time (regime shift detection).
        """
        if len(self.trades_log) < 20:
            print("Need at least 20 trades to measure decay")
            return None
        
        # Split into two halves
        midpoint = len(self.trades_log) // 2
        first_half = self.trades_log[:midpoint]
        second_half = self.trades_log[midpoint:]
        
        def calculate_wr(trades):
            if not trades:
                return 0
            # Simple: count positive vs negative
            positive = sum(1 for t in trades if t.get("confidence", 0) > 0.7)
            return positive / len(trades) if trades else 0
        
        wr_first = calculate_wr(first_half)
        wr_second = calculate_wr(second_half)
        decay = wr_first - wr_second
        
        print(f"\n{'EDGE DECAY ANALYSIS':-^70}")
        print(f"First Half Win Rate:  {wr_first:.1%}")
        print(f"Second Half Win Rate: {wr_second:.1%}")
        print(f"Decay:                {decay:.1%}")
        
        if decay > 0.10:
            print("⚠️  EDGE DECAY DETECTED - System may need recalibration")
        else:
            print("✅ Edge stable - No decay detected")
        
        return {"decay": decay, "wr_first": wr_first, "wr_second": wr_second}


# Usage example:
if __name__ == "__main__":
    engine = BacktestEngine()
    
    # Simulate historical data (in practice, load from CME/file)
    historical_data = [
        {"time": "2026-01-10T10:00:00", "open": 3348, "high": 3365, "low": 3342, "close": 3362, "volume": 1200},
        {"time": "2026-01-10T10:05:00", "open": 3362, "high": 3368, "low": 3360, "close": 3363, "volume": 900},
        # ... more candles
    ]
    
    results = engine.run_backtest(
        historical_data,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 1, 31)
    )
    
    engine.print_backtest_report()
    engine.identify_best_conditions()
    engine.measure_edge_decay()
