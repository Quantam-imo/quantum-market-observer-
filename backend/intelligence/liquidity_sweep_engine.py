"""
Liquidity Sweep Engine — Detects institutional liquidity hunts
When price breaks structure, hits liquidity, then reverses rapidly
This is pure ICT/SMC logic: the trap confirmation
"""

class LiquiditySweepEngine:
    """
    Detects liquidity sweeps from candlestick data.
    Sweep = Break + Rejection = Institutional trap
    """
    
    def __init__(self):
        self.sweep_history = []
        self.breached_levels = {}
    
    def detect(self, candles):
        """
        Detect liquidity sweeps by identifying breaks and immediate rejections.
        
        Args:
            candles: List of OHLC candles {high, low, close, open, time, volume}
        
        Returns:
            List of sweep events with direction and strength
        """
        if len(candles) < 2:
            return []
        
        sweeps = []
        
        for i in range(1, len(candles)):
            prev = candles[i-1]
            curr = candles[i]
            
            prev_high = prev.get("high")
            prev_low = prev.get("low")
            curr_high = curr.get("high")
            curr_low = curr.get("low")
            curr_close = curr.get("close")
            curr_open = curr.get("open")
            curr_time = curr.get("time", "N/A")
            curr_volume = curr.get("volume", 0)
            
            # BUY-SIDE SWEEP: Break above resistance, then close below
            if curr_high > prev_high and curr_close < prev_high:
                sweep = {
                    "type": "BUY_SIDE_SWEEP",
                    "level": prev_high,
                    "time": curr_time,
                    "break_level": curr_high,
                    "rejection_level": curr_close,
                    "wicks_above": curr_high - prev_high,
                    "volume": curr_volume,
                    "strength": self._calculate_strength(
                        break_above=curr_high - prev_high,
                        rejection=prev_high - curr_close,
                        volume=curr_volume
                    ),
                    "implication": "Retail longs trapped, liquidity taken"
                }
                sweeps.append(sweep)
                self.sweep_history.append(sweep)
                self.breached_levels[prev_high] = {"type": "BUY_TRAP", "time": curr_time}
            
            # SELL-SIDE SWEEP: Break below support, then close above
            elif curr_low < prev_low and curr_close > prev_low:
                sweep = {
                    "type": "SELL_SIDE_SWEEP",
                    "level": prev_low,
                    "time": curr_time,
                    "break_level": curr_low,
                    "rejection_level": curr_close,
                    "wicks_below": prev_low - curr_low,
                    "volume": curr_volume,
                    "strength": self._calculate_strength(
                        break_below=prev_low - curr_low,
                        rejection=curr_close - prev_low,
                        volume=curr_volume
                    ),
                    "implication": "Retail shorts trapped, liquidity taken"
                }
                sweeps.append(sweep)
                self.sweep_history.append(sweep)
                self.breached_levels[prev_low] = {"type": "SELL_TRAP", "time": curr_time}
        
        return sweeps
    
    def _calculate_strength(self, break_above=0, break_below=0, rejection=0, volume=0):
        """
        Calculate sweep strength (0.0 to 1.0) based on:
        - Size of break
        - Size of rejection
        - Volume confirmation
        """
        break_size = max(break_above, break_below)
        
        # Stronger if: large break + immediate rejection + high volume
        strength = min(1.0, (break_size * 0.4 + rejection * 0.4 + min(volume / 1000, 1.0) * 0.2))
        return round(strength, 3)
    
    def get_recent_sweeps(self, count=10):
        """Get the N most recent sweeps."""
        return self.sweep_history[-count:]
    
    def get_trapped_levels(self):
        """Get all levels where liquidity was taken (trapped traders)."""
        return self.breached_levels
    
    def is_near_trapped_level(self, price, tolerance=5):
        """
        Check if current price is near a previously trapped level.
        If true, institutions may defend or re-enter.
        """
        for level in self.breached_levels.keys():
            if abs(level - price) <= tolerance:
                return True, level, self.breached_levels[level]
        return False, None, None
