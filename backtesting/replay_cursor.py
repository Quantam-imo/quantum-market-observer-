# backtesting/replay_cursor.py
"""
ReplayCursor: Time-travel engine for replay scrubbing.

Allows stepping through replay candle-by-candle:
- next() — move forward
- prev() — move backward
- jump_to(index) — jump to specific candle
- current() — get current candle

Essential for professional signal debugging and visual scrubbing.
"""


class ReplayCursor:
    """Navigate through replay candles (time-travel)."""
    
    def __init__(self, candles, timeline=None):
        """
        Initialize cursor.
        
        Args:
            candles: List of candle dicts (time, open, high, low, close, volume)
            timeline: Optional timeline from TimelineBuilder for context lookup
        """
        self.candles = candles
        self.timeline = timeline or []
        self.index = 0
        self._position_history = []
    
    def next(self):
        """
        Move to next candle.
        
        Returns:
            Current candle dict, or None if at end
        """
        if self.index < len(self.candles) - 1:
            self._position_history.append(self.index)
            self.index += 1
            return self.current()
        return None
    
    def prev(self):
        """
        Move to previous candle.
        
        Returns:
            Current candle dict, or None if at start
        """
        if self.index > 0:
            self._position_history.append(self.index)
            self.index -= 1
            return self.current()
        return None
    
    def jump_to(self, index):
        """
        Jump to specific candle by index.
        
        Args:
            index: Target candle index (0-based)
        
        Returns:
            Current candle dict
        """
        self._position_history.append(self.index)
        self.index = max(0, min(index, len(self.candles) - 1))
        return self.current()
    
    def jump_to_time(self, target_time):
        """
        Jump to candle by time.
        
        Args:
            target_time: Datetime or timestamp to find
        
        Returns:
            Current candle dict, or None if time not found
        """
        for i, candle in enumerate(self.candles):
            if candle.get("time") == target_time:
                self._position_history.append(self.index)
                self.index = i
                return self.current()
        return None
    
    def current(self):
        """
        Get current candle.
        
        Returns:
            Current candle dict
        """
        if 0 <= self.index < len(self.candles):
            return self.candles[self.index]
        return None
    
    def current_context(self):
        """
        Get current candle + timeline context.
        
        Returns:
            Dict with candle and timeline entry
        """
        candle = self.current()
        context = None
        
        if self.timeline and candle:
            # Find matching timeline entry
            for entry in self.timeline:
                if entry.get("time") == candle.get("time"):
                    context = entry
                    break
        
        return {
            "candle": candle,
            "timeline": context,
            "index": self.index,
        }
    
    def get_index(self):
        """Return current index."""
        return self.index
    
    def get_position(self):
        """Return current position (index / total)."""
        return {
            "current": self.index + 1,
            "total": len(self.candles),
            "percentage": ((self.index + 1) / len(self.candles) * 100) if self.candles else 0,
        }
    
    def is_at_start(self):
        """Return True if at first candle."""
        return self.index == 0
    
    def is_at_end(self):
        """Return True if at last candle."""
        return self.index == len(self.candles) - 1
    
    def rewind(self):
        """Go back to first candle."""
        self._position_history.append(self.index)
        self.index = 0
        return self.current()
    
    def fast_forward(self):
        """Go to last candle."""
        self._position_history.append(self.index)
        self.index = len(self.candles) - 1
        return self.current()
    
    def get_navigation_history(self):
        """Return history of positions visited."""
        return self._position_history
    
    def peek_forward(self, steps=1):
        """
        Look ahead without moving.
        
        Args:
            steps: Number of candles ahead
        
        Returns:
            Future candle dict, or None if beyond bounds
        """
        future_index = self.index + steps
        if 0 <= future_index < len(self.candles):
            return self.candles[future_index]
        return None
    
    def peek_backward(self, steps=1):
        """
        Look back without moving.
        
        Args:
            steps: Number of candles back
        
        Returns:
            Past candle dict, or None if before start
        """
        past_index = self.index - steps
        if 0 <= past_index < len(self.candles):
            return self.candles[past_index]
        return None
    
    def get_range(self, start_index, end_index):
        """
        Get range of candles.
        
        Args:
            start_index: Start (inclusive)
            end_index: End (inclusive)
        
        Returns:
            List of candles in range
        """
        start = max(0, start_index)
        end = min(len(self.candles), end_index + 1)
        return self.candles[start:end]
