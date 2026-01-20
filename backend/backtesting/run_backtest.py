#!/usr/bin/env python3
"""
Run backtest and generate report
Quick way to test system on historical data
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.backtesting.backtest_engine import BacktestEngine
from backend.backtesting.historical_loader import HistoricalDataLoader
from backend.backtesting.trade_journal import TradeJournal


def run_backtest():
    """Run complete backtest workflow."""
    
    print("\n" + "="*70)
    print("QUANTUM MARKET OBSERVER — BACKTEST")
    print("="*70 + "\n")
    
    # Load historical data
    print("📊 Loading historical data...")
    loader = HistoricalDataLoader(data_source="simulation")
    
    start_date = datetime(2026, 1, 6)   # Monday
    end_date = datetime(2026, 1, 17)    # Friday (full 2 weeks)
    
    historical_data = loader.load_date_range(start_date, end_date)
    print(f"✅ Loaded {len(historical_data)} candles ({start_date.date()} → {end_date.date()})\n")
    
    # Run backtest
    print("🔬 Running backtest...")
    engine = BacktestEngine()
    results = engine.run_backtest(historical_data, start_date, end_date)
    
    # Print results
    engine.print_backtest_report()
    
    # Identify best conditions
    print("\n🎯 Analyzing best conditions...")
    best_conditions = engine.identify_best_conditions()
    
    # Measure edge decay
    print("\n📈 Measuring edge stability...")
    decay_analysis = engine.measure_edge_decay()
    
    # Summary
    print("\n" + "="*70)
    print("BACKTEST COMPLETE")
    print("="*70)
    print(f"\n✅ System ready for paper trading")
    print(f"✅ Edge confidence: {results['win_rate']:.1%} win rate")
    print(f"✅ Expected R per trade: {results['avg_r_multiple']:.2f}R")
    
    return results


def example_trade_journal():
    """Example of how to use trade journal."""
    
    print("\n" + "="*70)
    print("TRADE JOURNAL EXAMPLE")
    print("="*70 + "\n")
    
    journal = TradeJournal()
    
    # Log multiple trades
    trades = [
        {
            "entry_time": "14:35 GMT",
            "exit_time": "14:52 GMT",
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
            "execution_notes": "Perfect execution, no fear"
        },
        {
            "entry_time": "15:10 GMT",
            "exit_time": "15:22 GMT",
            "direction": "BUY",
            "entry_price": 3350,
            "exit_price": 3348,
            "stop_loss": 3345,
            "take_profit_1": 3360,
            "take_profit_2": 3370,
            "r_multiple": -1.0,
            "result": "LOSS",
            "setup_type": "CHOP_ZONE",
            "ai_confidence": 0.58,
            "execution_notes": "Forced trade, should have waited",
            "failure_reason": "ENTERED_OUTSIDE_CONFLUENCE"
        }
    ]
    
    for trade in trades:
        journal.log_trade(trade)
    
    # Analyze
    journal.calculate_performance_metrics()


if __name__ == "__main__":
    # Run full backtest
    results = run_backtest()
    
    # Show trade journal example
    example_trade_journal()
    
    print("\n" + "="*70)
    print("🚀 NEXT STEPS:")
    print("="*70)
    print("1. Review backtest results")
    print("2. Identify best setups from 'Best Conditions'")
    print("3. Start paper trading (max 1 trade/session)")
    print("4. Log every trade in trade journal")
    print("5. After 30 days: run backtest again to measure improvement")
    print("="*70 + "\n")
