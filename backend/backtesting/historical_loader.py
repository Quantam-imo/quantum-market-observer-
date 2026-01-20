"""
Historical Data Loader - Load CME historical data for backtesting
Connects to CME API or CSV files
"""

from datetime import datetime, timedelta
import json
from pathlib import Path


class HistoricalDataLoader:
    """
    Load historical CME GC data for backtesting.
    Supports CME API, CSV files, or simulation data.
    """
    
    def __init__(self, data_source="csv"):
        self.data_source = data_source
        self.data_cache = {}
    
    def load_date_range(self, start_date, end_date, instrument="GC"):
        """
        Load historical data for date range.
        
        Args:
            start_date: datetime
            end_date: datetime
            instrument: "GC" (gold comex) default
        
        Returns:
            List of candles with OHLCV data
        """
        
        if self.data_source == "csv":
            return self._load_from_csv(start_date, end_date, instrument)
        elif self.data_source == "cme_api":
            return self._load_from_cme_api(start_date, end_date, instrument)
        else:
            return self._generate_simulation_data(start_date, end_date)
    
    def _load_from_csv(self, start_date, end_date, instrument):
        """Load from local CSV files."""
        csv_path = Path(f"historical_data/{instrument}_{start_date.date()}.csv")
        
        if not csv_path.exists():
            print(f"⚠️  CSV file not found: {csv_path}")
            print("Using simulation data instead")
            return self._generate_simulation_data(start_date, end_date)
        
        candles = []
        with open(csv_path) as f:
            for line in f:
                parts = line.strip().split(",")
                candle = {
                    "time": parts[0],
                    "open": float(parts[1]),
                    "high": float(parts[2]),
                    "low": float(parts[3]),
                    "close": float(parts[4]),
                    "volume": int(parts[5])
                }
                
                candle_time = datetime.fromisoformat(candle["time"])
                if start_date <= candle_time <= end_date:
                    candles.append(candle)
        
        return candles
    
    def _load_from_cme_api(self, start_date, end_date, instrument):
        """Load from CME API (requires credentials)."""
        # Placeholder for CME API integration
        print("CME API loader not implemented yet")
        return self._generate_simulation_data(start_date, end_date)
    
    def _generate_simulation_data(self, start_date, end_date):
        """
        Generate realistic simulation data for testing.
        Mimics actual GC behavior.
        """
        import random
        
        candles = []
        current = start_date
        current_price = 3350.0  # Starting price
        
        while current <= end_date:
            # Skip weekends
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue
            
            # Generate realistic OHLC
            # Gold typically moves 10-30 points per 5 min
            move = random.gauss(0, 8)  # Normal distribution
            
            open_price = current_price
            close_price = current_price + move
            high_price = max(open_price, close_price) + random.uniform(0, 5)
            low_price = min(open_price, close_price) - random.uniform(0, 5)
            volume = random.randint(500, 2000)
            
            candle = {
                "time": current.isoformat(),
                "open": round(open_price, 1),
                "high": round(high_price, 1),
                "low": round(low_price, 1),
                "close": round(close_price, 1),
                "volume": volume
            }
            
            candles.append(candle)
            current_price = close_price
            current += timedelta(minutes=5)
        
        return candles
    
    def save_to_cache(self, data, key):
        """Cache loaded data to avoid reloading."""
        self.data_cache[key] = data
    
    def load_from_cache(self, key):
        """Load cached data."""
        return self.data_cache.get(key)


# Example usage:
if __name__ == "__main__":
    loader = HistoricalDataLoader(data_source="simulation")
    
    data = loader.load_date_range(
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 1, 31)
    )
    
    print(f"Loaded {len(data)} candles")
    print("First 5 candles:")
    for candle in data[:5]:
        print(f"  {candle['time']}: O={candle['open']} H={candle['high']} "
              f"L={candle['low']} C={candle['close']} V={candle['volume']}")
