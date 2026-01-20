"""
CME Data Simulator - Generates realistic CME COMEX Gold futures data for testing
Simulates market conditions with iceberg patterns
"""

from typing import List, Dict
from datetime import datetime, timedelta
import random
import math


class CMESimulator:
    """
    Generates realistic CME market data for backtesting/simulation.
    Creates patterns that include:
    - Normal price movement
    - Volume spikes (iceberg activity)
    - Realistic bid/ask spreads
    - Session transitions
    """
    
    def __init__(self, start_price: float = 2450.50):
        self.price = start_price
        self.bid = start_price - 0.2
        self.ask = start_price + 0.2
        self.timestamp = datetime.utcnow()
        self.volume_base = 1000
        
    def generate_trade(self) -> Dict:
        """Generate single realistic trade."""
        # Random walk
        price_move = random.gauss(0, 0.5)  # Normal distribution
        self.price += price_move
        
        # Size: normal trade 50-200 contracts, occasional spike
        if random.random() < 0.05:  # 5% chance of large trade
            size = random.randint(300, 800)  # Iceberg potential
        else:
            size = random.randint(50, 200)
        
        side = "BUY" if random.random() > 0.5 else "SELL"
        
        trade = {
            "type": "TRADE",
            "price": round(self.price, 1),
            "size": size,
            "side": side,
            "timestamp": self.timestamp.isoformat() + "Z"
        }
        
        self.timestamp += timedelta(milliseconds=random.randint(10, 500))
        return trade
    
    def generate_trades_batch(self, count: int = 50) -> List[Dict]:
        """Generate batch of trades."""
        return [self.generate_trade() for _ in range(count)]
    
    def generate_quote(self) -> Dict:
        """Generate bid/ask quote."""
        # Spread varies: 0.1-0.5 normally
        spread = random.uniform(0.1, 0.3)
        
        self.bid = round(self.price - spread/2, 1)
        self.ask = round(self.price + spread/2, 1)
        
        # Volume imbalance
        bid_size = random.randint(100, 500)
        ask_size = random.randint(100, 500)
        
        # Occasional imbalance (iceberg signal)
        if random.random() < 0.1:
            if random.random() > 0.5:
                bid_size *= 3
            else:
                ask_size *= 3
        
        quote = {
            "type": "QUOTE",
            "bid_price": self.bid,
            "ask_price": self.ask,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "timestamp": self.timestamp.isoformat() + "Z"
        }
        
        return quote
    
    def generate_ohlc(self, interval_minutes: int = 60) -> Dict:
        """Generate candlestick data."""
        open_p = self.price
        
        # Generate random moves
        high = open_p + abs(random.gauss(0, 2))
        low = open_p - abs(random.gauss(0, 2))
        close = random.uniform(low, high)
        
        # Volume correlates with range
        range_size = high - low
        volume = int(self.volume_base * (1 + range_size / 10))
        
        ohlc = {
            "type": "OHLC",
            "open": round(open_p, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": volume,
            "interval": f"{interval_minutes}m",
            "timestamp": self.timestamp.isoformat() + "Z"
        }
        
        self.price = close
        self.timestamp += timedelta(minutes=interval_minutes)
        
        return ohlc
    
    def generate_iceberg_pattern(self) -> List[Dict]:
        """
        Generate trades showing iceberg order signature.
        
        Pattern:
        1. Price moving down steadily
        2. Sudden large buy volume
        3. Price stabilizes/reverses
        """
        trades = []
        
        # Phase 1: downside movement
        for i in range(15):
            self.price -= 0.3
            trades.append({
                "type": "TRADE",
                "price": round(self.price, 1),
                "size": random.randint(50, 150),
                "side": "SELL",
                "timestamp": self.timestamp.isoformat() + "Z"
            })
            self.timestamp += timedelta(milliseconds=300)
        
        # Phase 2: ABSORPTION - large buy volume
        for i in range(5):
            trades.append({
                "type": "TRADE",
                "price": round(self.price, 1),
                "size": random.randint(300, 600),  # Much larger
                "side": "BUY",
                "timestamp": self.timestamp.isoformat() + "Z"
            })
            self.timestamp += timedelta(milliseconds=100)
        
        # Phase 3: stabilization
        for i in range(10):
            self.price += 0.1
            trades.append({
                "type": "TRADE",
                "price": round(self.price, 1),
                "size": random.randint(50, 100),
                "side": "BUY" if random.random() > 0.5 else "SELL",
                "timestamp": self.timestamp.isoformat() + "Z"
            })
            self.timestamp += timedelta(milliseconds=400)
        
        return trades
    
    def generate_session(self, session_name: str = "LONDON", minutes: int = 60) -> List[Dict]:
        """
        Generate realistic session data.
        
        Sessions have different characteristics:
        - ASIA: often quiet consolidation
        - LONDON: active, ranges break
        - NEWYORK: volatility, adjustments
        """
        data = []
        
        # Volatility multiplier per session
        volatility = {
            "ASIA": 0.8,
            "LONDON": 1.2,
            "NEWYORK": 1.5,
            "OVERNIGHT": 0.6
        }
        
        vol_mult = volatility.get(session_name, 1.0)
        
        # Generate minute-by-minute data
        for minute in range(minutes):
            # Quote every 5 seconds
            if minute % 5 == 0:
                data.append(self.generate_quote())
            
            # Trades every second
            for _ in range(60):
                trade = self.generate_trade()
                trade["price"] = round(trade["price"] * vol_mult, 1)
                data.append(trade)
                self.timestamp += timedelta(seconds=1)
        
        # End-of-session OHLC
        data.append(self.generate_ohlc(interval_minutes=60))
        
        return data


def create_test_scenario(scenario_type: str = "normal") -> List[Dict]:
    """
    Create specific test scenarios.
    
    Scenarios:
    - "normal": Regular market
    - "iceberg": Iceberg absorption activity
    - "volatile": High volatility session
    """
    
    sim = CMESimulator(start_price=2450.50)
    
    if scenario_type == "normal":
        return sim.generate_trades_batch(100)
    
    elif scenario_type == "iceberg":
        return sim.generate_iceberg_pattern()
    
    elif scenario_type == "volatile":
        trades = []
        for i in range(10):
            trades.extend(sim.generate_iceberg_pattern())
        return trades
    
    else:
        return sim.generate_session("LONDON", minutes=30)


# Convenience function for API testing
def get_sample_cme_data() -> List[Dict]:
    """Get sample CME data for immediate testing."""
    return create_test_scenario("normal")
