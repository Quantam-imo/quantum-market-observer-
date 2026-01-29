"""
Volume Profile Engine - Advanced Volume Distribution Analysis with Buy/Sell Tracking

Calculates:
- POC (Point of Control): Price level with highest volume
- VAH (Value Area High): Upper bound of 70% volume area
- VAL (Value Area Low): Lower bound of 70% volume area
- Volume distribution histogram for visualization
- VWAP (Volume Weighted Average Price)
- Buy/Sell volume breakdown
"""

from typing import List, Dict, Any
from collections import defaultdict


class VolumeProfileEngine:
    def __init__(self, tick_size: float = 0.10):
        """
        Initialize Volume Profile Engine
        
        Args:
            tick_size: Price granularity for volume clustering (default 0.10 for gold futures)
        """
        self.profile = {}
        self.tick_size = tick_size
        self.volume_by_price = {}
        
    def build_profile(self, candles: List[Dict[str, Any]], value_area_pct: float = 0.70) -> Dict[str, Any]:
        """
        Build volume profile from OHLC candles
        
        Args:
            candles: List of OHLC candle dictionaries with keys: open, high, low, close, volume
            value_area_pct: Percentage for value area calculation (default 0.70 = 70%)
            
        Returns:
            Dictionary containing POC, VAH, VAL, VWAP, and histogram data
        """
        if not candles:
            return {
                "POC": 0,
                "VAH": 0,
                "VAL": 0,
                "VWAP": 0,
                "histogram": [],
                "total_volume": 0,
                "total_buy_volume": 0,
                "total_sell_volume": 0
            }
        
        volume_by_price = defaultdict(float)
        buy_volume_by_price = defaultdict(float)
        sell_volume_by_price = defaultdict(float)
        total_volume = 0
        total_buy_volume = 0
        total_sell_volume = 0
        vwap_numerator = 0
        
        # Distribute volume across price range of each candle
        for candle in candles:
            high = candle.get("high", candle.get("close", 0))
            low = candle.get("low", candle.get("close", 0))
            close = candle.get("close", 0)
            open_price = candle.get("open", close)
            volume = candle.get("volume", 0)
            
            if volume == 0 or high == 0:
                continue
            
            # Determine if bullish (buy) or bearish (sell) candle
            is_bullish = close >= open_price
            
            # Calculate typical price for VWAP
            typical_price = (high + low + close) / 3
            vwap_numerator += typical_price * volume
            total_volume += volume
            
            if is_bullish:
                total_buy_volume += volume
            else:
                total_sell_volume += volume
            
            # Distribute volume across price range using tick size
            price_range = high - low
            if price_range == 0:
                # Single price point
                price_level = self._round_to_tick(close)
                volume_by_price[price_level] += volume
                if is_bullish:
                    buy_volume_by_price[price_level] += volume
                else:
                    sell_volume_by_price[price_level] += volume
            else:
                # Distribute volume proportionally across range
                num_ticks = max(1, int(price_range / self.tick_size))
                volume_per_tick = volume / num_ticks
                
                current_price = low
                while current_price <= high:
                    price_level = self._round_to_tick(current_price)
                    volume_by_price[price_level] += volume_per_tick
                    if is_bullish:
                        buy_volume_by_price[price_level] += volume_per_tick
                    else:
                        sell_volume_by_price[price_level] += volume_per_tick
                    current_price += self.tick_size
        
        if not volume_by_price or total_volume == 0:
            return {
                "POC": 0,
                "VAH": 0,
                "VAL": 0,
                "VWAP": 0,
                "histogram": [],
                "total_volume": 0,
                "total_buy_volume": 0,
                "total_sell_volume": 0
            }
        
        # Calculate VWAP
        vwap = vwap_numerator / total_volume if total_volume > 0 else 0
        
        # Find POC (Point of Control) - price with highest volume
        poc = max(volume_by_price.items(), key=lambda x: x[1])[0]
        
        # Calculate Value Area (70% of volume around POC)
        sorted_prices = sorted(volume_by_price.keys())
        value_area_volume = total_volume * value_area_pct
        
        # Start from POC and expand outward to capture value_area_pct of volume
        vah, val = self._calculate_value_area(volume_by_price, poc, value_area_volume)
        
        # Build histogram for frontend visualization
        histogram = []
        max_volume = max(volume_by_price.values())
        
        for price in sorted(volume_by_price.keys()):
            volume = volume_by_price[price]
            buy_vol = buy_volume_by_price.get(price, 0)
            sell_vol = sell_volume_by_price.get(price, 0)
            histogram.append({
                "price": round(price, 2),
                "volume": int(volume),
                "buy_volume": int(buy_vol),
                "sell_volume": int(sell_vol),
                "volume_pct": round((volume / max_volume) * 100, 2),
                "is_poc": price == poc,
                "in_value_area": val <= price <= vah
            })
        
        self.profile = {
            "POC": round(poc, 2),
            "VAH": round(vah, 2),
            "VAL": round(val, 2),
            "VWAP": round(vwap, 2),
            "histogram": histogram,
            "total_volume": int(total_volume),
            "total_buy_volume": int(total_buy_volume),
            "total_sell_volume": int(total_sell_volume),
            "value_area_pct": int(value_area_pct * 100)
        }
        
        self.volume_by_price = dict(volume_by_price)
        
        return self.profile
    
    def _round_to_tick(self, price: float) -> float:
        """Round price to nearest tick size"""
        return round(price / self.tick_size) * self.tick_size
    
    def _calculate_value_area(self, volume_by_price: Dict[float, float], poc: float, target_volume: float) -> tuple:
        """
        Calculate Value Area High (VAH) and Value Area Low (VAL)
        
        Expands from POC outward until capturing target_volume
        """
        accumulated_volume = volume_by_price[poc]
        val = vah = poc
        
        sorted_prices = sorted(volume_by_price.keys())
        poc_index = sorted_prices.index(poc)
        
        lower_index = poc_index - 1
        upper_index = poc_index + 1
        
        # Expand outward from POC
        while accumulated_volume < target_volume:
            lower_vol = volume_by_price.get(sorted_prices[lower_index], 0) if lower_index >= 0 else 0
            upper_vol = volume_by_price.get(sorted_prices[upper_index], 0) if upper_index < len(sorted_prices) else 0
            
            if lower_vol == 0 and upper_vol == 0:
                break
            
            # Add the side with more volume
            if lower_vol >= upper_vol and lower_index >= 0:
                accumulated_volume += lower_vol
                val = sorted_prices[lower_index]
                lower_index -= 1
            elif upper_index < len(sorted_prices):
                accumulated_volume += upper_vol
                vah = sorted_prices[upper_index]
                upper_index += 1
            else:
                break
        
        return vah, val
    
    def get_poc(self) -> float:
        """Get Point of Control (POC)"""
        return self.profile.get("POC", 0)
    
    def get_value_area(self) -> tuple:
        """Get Value Area High and Low (VAH, VAL)"""
        return self.profile.get("VAH", 0), self.profile.get("VAL", 0)
    
    def get_vwap(self) -> float:
        """Get Volume Weighted Average Price (VWAP)"""
        return self.profile.get("VWAP", 0)
    
    def is_price_in_value_area(self, price: float) -> bool:
        """Check if price is within value area"""
        val, vah = self.get_value_area()
        return val <= price <= vah
