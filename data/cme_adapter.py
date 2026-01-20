"""
CME Data Adapter - Normalizes raw CME COMEX Gold futures feed
Converts GC prices to XAUUSD equivalent
Handles market data normalization
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CMEAdapter:
    """
    Converts raw CME market data into normalized format.
    Handles:
    - Price normalization
    - Volume aggregation
    - Delta calculation
    - Session tracking
    """
    
    def __init__(self):
        self.session_state = None
        self.last_close = None
        self.bid_volume = 0
        self.ask_volume = 0
        
    def normalize_trade(self, msg: Dict) -> Optional[Dict]:
        """
        Convert raw CME trade message to standard format.
        
        Expected CME format:
        {
            "price": 3362.4,
            "size": 150,
            "side": "BUY" | "SELL",
            "timestamp": "2026-01-17T14:30:45.123Z",
            "sequence": 12345
        }
        """
        try:
            trade = {
                "price": float(msg.get("price", 0)),
                "size": int(msg.get("size", 0)),
                "side": msg.get("side", "UNKNOWN").upper(),
                "timestamp": msg.get("timestamp", datetime.utcnow().isoformat()),
                "sequence": msg.get("sequence", 0),
                "exchange": "CME",
                "symbol": "GC"  # Gold Futures
            }
            
            # Validate
            if trade["price"] <= 0 or trade["size"] <= 0:
                logger.warning(f"Invalid trade data: {msg}")
                return None
                
            return trade
            
        except Exception as e:
            logger.error(f"Error normalizing trade: {e}")
            return None

    def normalize_quote(self, msg: Dict) -> Optional[Dict]:
        """
        Convert CME bid/ask quote.
        
        Expected format:
        {
            "bid_price": 3362.2,
            "ask_price": 3362.5,
            "bid_size": 250,
            "ask_size": 300,
            "timestamp": "2026-01-17T14:30:45Z"
        }
        """
        try:
            quote = {
                "bid": float(msg.get("bid_price", 0)),
                "ask": float(msg.get("ask_price", 0)),
                "bid_volume": int(msg.get("bid_size", 0)),
                "ask_volume": int(msg.get("ask_size", 0)),
                "spread": float(msg.get("ask_price", 0)) - float(msg.get("bid_price", 0)),
                "mid": (float(msg.get("bid_price", 0)) + float(msg.get("ask_price", 0))) / 2,
                "timestamp": msg.get("timestamp", datetime.utcnow().isoformat()),
                "exchange": "CME",
                "symbol": "GC"
            }
            
            # Track for delta calculation
            self.bid_volume = quote["bid_volume"]
            self.ask_volume = quote["ask_volume"]
            
            return quote
            
        except Exception as e:
            logger.error(f"Error normalizing quote: {e}")
            return None

    def normalize_ohlc(self, msg: Dict) -> Optional[Dict]:
        """
        Convert CME OHLC (candle) data.
        
        Expected format:
        {
            "open": 3360.0,
            "high": 3365.5,
            "low": 3358.2,
            "close": 3362.1,
            "volume": 45000,
            "timestamp": "2026-01-17T14:30:00Z",
            "interval": "1H"  # or 5m, 15m, etc
        }
        """
        try:
            ohlc = {
                "open": float(msg.get("open", 0)),
                "high": float(msg.get("high", 0)),
                "low": float(msg.get("low", 0)),
                "close": float(msg.get("close", 0)),
                "volume": int(msg.get("volume", 0)),
                "timestamp": msg.get("timestamp", datetime.utcnow().isoformat()),
                "interval": msg.get("interval", "1H"),
                "range": float(msg.get("high", 0)) - float(msg.get("low", 0)),
                "exchange": "CME",
                "symbol": "GC"
            }
            
            # Store for delta calculation
            self.last_close = ohlc["close"]
            
            return ohlc
            
        except Exception as e:
            logger.error(f"Error normalizing OHLC: {e}")
            return None

    def gc_to_xauusd(self, gc_price: float) -> float:
        """
        Map GC futures price to XAUUSD equivalent.
        
        Institutional reality:
        - GC and XAUUSD track nearly 1:1
        - Spread differences reconciled at execution layer
        - For analysis: GC price ≈ XAUUSD price
        
        Formula: XAUUSD = GC (approximately)
        """
        if gc_price <= 0:
            return 0
        return round(gc_price, 2)

    def calculate_delta(self, buy_volume: int, sell_volume: int) -> int:
        """
        Calculate delta (Buy Volume - Sell Volume).
        
        Used to detect:
        - Institutional aggression (delta > 0 = buying)
        - Absorption zones (small delta at price extremes)
        - Momentum direction
        """
        return buy_volume - sell_volume

    def detect_session(self, timestamp: str) -> str:
        """
        Detect current trading session from timestamp.
        
        CME Gold sessions:
        - Asia: 17:00-02:00 UTC (Tokyo open)
        - London: 08:00-17:00 UTC
        - NY: 13:00-22:00 UTC
        - Overnight: 22:00-17:00 UTC
        """
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            
            if 17 <= hour or hour < 2:
                return "ASIA"
            elif 8 <= hour < 17:
                return "LONDON"
            elif 13 <= hour < 22:
                return "NEWYORK"
            else:
                return "OVERNIGHT"
                
        except Exception as e:
            logger.error(f"Error detecting session: {e}")
            return "UNKNOWN"

    def stream_processor(self, raw_messages: List[Dict]) -> Dict:
        """
        Process batch of CME messages and aggregate state.
        
        Returns current market snapshot.
        """
        processed = {
            "trades": [],
            "quotes": [],
            "ohlc": None,
            "aggregated": {
                "total_volume": 0,
                "buy_volume": 0,
                "sell_volume": 0,
                "delta": 0,
                "mid_price": 0,
                "spread": 0,
                "session": "UNKNOWN"
            }
        }
        
        buy_vol = 0
        sell_vol = 0
        total_vol = 0
        prices = []
        
        for msg in raw_messages:
            msg_type = msg.get("type", "").upper()
            
            if msg_type == "TRADE":
                trade = self.normalize_trade(msg)
                if trade:
                    processed["trades"].append(trade)
                    total_vol += trade["size"]
                    
                    if trade["side"] == "BUY":
                        buy_vol += trade["size"]
                    else:
                        sell_vol += trade["size"]
                    
                    prices.append(trade["price"])
                    
            elif msg_type == "QUOTE":
                quote = self.normalize_quote(msg)
                if quote:
                    processed["quotes"].append(quote)
                    
            elif msg_type == "OHLC" or msg_type == "CANDLE":
                ohlc = self.normalize_ohlc(msg)
                if ohlc:
                    processed["ohlc"] = ohlc
        
        # Aggregate
        if prices:
            processed["aggregated"]["mid_price"] = sum(prices) / len(prices)
        
        processed["aggregated"]["total_volume"] = total_vol
        processed["aggregated"]["buy_volume"] = buy_vol
        processed["aggregated"]["sell_volume"] = sell_vol
        processed["aggregated"]["delta"] = buy_vol - sell_vol
        processed["aggregated"]["spread"] = 0.1  # Default CME GC spread
        
        if raw_messages:
            processed["aggregated"]["session"] = self.detect_session(
                raw_messages[0].get("timestamp", "")
            )
        
        return processed


class GCPriceCache:
    """
    Caches recent GC prices for quick analysis.
    Maintains rolling window for Gann/Astro calculations.
    """
    
    def __init__(self, max_bars: int = 1000):
        self.max_bars = max_bars
        self.prices = []
        self.timestamps = []
        
    def add(self, price: float, timestamp: str):
        """Add price to cache."""
        self.prices.append(price)
        self.timestamps.append(timestamp)
        
        # Keep only recent bars
        if len(self.prices) > self.max_bars:
            self.prices.pop(0)
            self.timestamps.pop(0)
    
    def get_high_low(self, bars: int = 50) -> tuple:
        """Get high/low over N bars."""
        if not self.prices or bars > len(self.prices):
            return None, None
        
        recent = self.prices[-bars:]
        return max(recent), min(recent)
    
    def get_range(self, bars: int = 50) -> float:
        """Get price range over N bars."""
        high, low = self.get_high_low(bars)
        if high is None or low is None:
            return 0
        return high - low
