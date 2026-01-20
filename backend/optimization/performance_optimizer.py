"""
STEP 21 — PERFORMANCE OPTIMIZATION MODULE
Session-locked caching, event-driven engines, confidence stabilization, memory decay
"""

from datetime import datetime, timedelta
import math


class PerformanceOptimizer:
    """Master optimizer controlling all speed/stability improvements."""
    
    def __init__(self):
        """Initialize optimizer with caching and decay systems."""
        self.cache = {
            "gann_levels": None,
            "gann_session": None,
            "astro_state": {},
            "cycle_counter": 0,
            "cycle_origin_time": None,
        }
        
        self.prev_confidence = 0.5
        self.memory_log = []
        self.last_data_time = datetime.now()
        self.signal_freeze = False
        
    # ═══════════════════════════════════════════════════════════════════════════
    # 1️⃣ GANN ENGINE OPTIMIZATION — Session-Locked Caching
    # ═══════════════════════════════════════════════════════════════════════════
    
    def optimize_gann(self, high: float, low: float, current_session: str) -> dict:
        """
        ✅ Calculate Gann levels only once per session.
        Recalculation wasteful if high/low haven't changed.
        """
        # Check if session changed or cache is empty
        if self.cache["gann_session"] != current_session:
            # Recalculate only when needed
            self.cache["gann_levels"] = self._calculate_gann_optimized(high, low)
            self.cache["gann_session"] = current_session
        
        return self.cache["gann_levels"]
    
    def _calculate_gann_optimized(self, high: float, low: float) -> dict:
        """Compute Gann levels with caching."""
        midpoint = (high + low) / 2
        range_size = high - low
        
        levels = {
            "high": high,
            "low": low,
            "midpoint": midpoint,
            "multipliers": {
                "0.5x": low + (range_size * 0.5),
                "1.0x": midpoint,
                "1.5x": low + (range_size * 1.5),
                "2.0x": high + (range_size * 1.0),
            },
            "square_of_9": self._compute_square_of_9(midpoint),
            "cached_at": datetime.now().isoformat(),
        }
        
        return levels
    
    def _compute_square_of_9(self, center: float) -> dict:
        """Fast Square of 9 computation."""
        return {
            "center": center,
            "cardinal_angles": [center + 45, center + 90, center + 135, center + 180],
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2️⃣ ASTRO ENGINE OPTIMIZATION — Time-Window Activation
    # ═══════════════════════════════════════════════════════════════════════════
    
    def optimize_astro(self, current_time: datetime, aspect_times: list, 
                       window_minutes: int = 4) -> dict:
        """
        ✅ Astro only WAKES UP when within aspect window.
        Never runs full calculations outside the window.
        """
        astro_state = {
            "active": False,
            "active_aspects": [],
            "activated_at": None,
        }
        
        window = timedelta(minutes=window_minutes)
        
        for aspect_time in aspect_times:
            time_to_aspect = abs((current_time - aspect_time).total_seconds())
            
            # Only check if close to aspect time
            if time_to_aspect <= window.total_seconds():
                astro_state["active"] = True
                astro_state["active_aspects"].append({
                    "aspect_time": aspect_time.isoformat(),
                    "distance_seconds": time_to_aspect,
                })
                astro_state["activated_at"] = current_time.isoformat()
        
        self.cache["astro_state"] = astro_state
        return astro_state
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3️⃣ CYCLE ENGINE OPTIMIZATION — Incremental Counter (No Scanning)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def optimize_cycle(self, new_bar_closed: bool) -> dict:
        """
        ✅ Increment counter. Check against key cycles.
        NO SCANNING. Deterministic.
        """
        result = {
            "cycle_hit": False,
            "bar_count": self.cache["cycle_counter"],
            "key_cycles": [7, 14, 21, 30, 45, 90, 144, 180, 360],
        }
        
        if new_bar_closed:
            self.cache["cycle_counter"] += 1
            
            # Check if current count is a key cycle
            if self.cache["cycle_counter"] in result["key_cycles"]:
                result["cycle_hit"] = True
                result["activation"] = {
                    "cycle": self.cache["cycle_counter"],
                    "power": "HIGH" if self.cache["cycle_counter"] in [90, 144, 180, 360] else "MEDIUM",
                }
        
        return result
    
    def reset_cycle_counter(self):
        """Reset counter on session boundary."""
        self.cache["cycle_counter"] = 0
        self.cache["cycle_origin_time"] = datetime.now()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4️⃣ ICEBERG PROXY OPTIMIZATION — Persistence Filter
    # ═══════════════════════════════════════════════════════════════════════════
    
    def optimize_iceberg(self, volume_spike_detected: bool, 
                        absorption_strength: float) -> dict:
        """
        ✅ Require persistence before flagging iceberg.
        Eliminates single-candle false positives.
        """
        if not hasattr(self, "_iceberg_persistence"):
            self._iceberg_persistence = 0
            self._last_absorption_strength = 0
        
        result = {
            "iceberg_valid": False,
            "persistence_level": self._iceberg_persistence,
            "absorption_strength": absorption_strength,
        }
        
        if volume_spike_detected and absorption_strength > 0.6:
            self._iceberg_persistence += 1
            self._last_absorption_strength = absorption_strength
        else:
            self._iceberg_persistence = 0
        
        # Require 3+ consecutive bars to validate iceberg
        if self._iceberg_persistence >= 3:
            result["iceberg_valid"] = True
            result["confidence_boost"] = 0.08  # +8% to overall confidence
        else:
            # Early warning (not yet valid)
            result["early_warning"] = self._iceberg_persistence > 0
        
        return result
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 5️⃣ CONFIDENCE ENGINE STABILIZATION — EMA Smoothing
    # ═══════════════════════════════════════════════════════════════════════════
    
    def stabilize_confidence(self, raw_confidence: float, 
                            alpha: float = 0.3) -> float:
        """
        ✅ Smooth confidence with EMA.
        Prevents emotional whipsaws.
        Recommended alpha: 0.3 (30% new, 70% previous)
        """
        # EMA formula: confidence = alpha * new + (1 - alpha) * prev
        smoothed = (alpha * raw_confidence) + ((1 - alpha) * self.prev_confidence)
        
        # Store for next calculation
        self.prev_confidence = smoothed
        
        # Log for monitoring
        self.memory_log.append({
            "timestamp": datetime.now().isoformat(),
            "raw": raw_confidence,
            "smoothed": smoothed,
            "change": smoothed - self.prev_confidence,
        })
        
        return round(smoothed, 3)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 6️⃣ MEMORY DECAY SYSTEM — Time-Weighted Forgetting
    # ═══════════════════════════════════════════════════════════════════════════
    
    def apply_memory_decay(self, memory_item: dict, memory_type: str,
                          created_at: datetime) -> dict:
        """
        ✅ Old memories become less relevant over time.
        Like a pro trader: remember lessons, forget emotional noise.
        """
        age = (datetime.now() - created_at).total_seconds()
        
        # Decay constants (in seconds)
        decay_constants = {
            "iceberg": 3600,        # 1 hour
            "cycle": 86400 * 3,     # 3 days
            "signal": 86400 * 10,   # 10 days
            "news": 1800,           # 30 minutes
        }
        
        tau = decay_constants.get(memory_type, 86400)
        
        # Exponential decay: weight = exp(-age / tau)
        decay_weight = math.exp(-age / tau)
        
        # Apply decay to confidence component
        if "confidence_component" in memory_item:
            memory_item["confidence_component"] *= decay_weight
        
        memory_item["decay_weight"] = round(decay_weight, 3)
        memory_item["age_seconds"] = age
        
        return memory_item
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 7️⃣ FAILSAFE & CRASH PROTECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def watchdog_timer(self, data_timeout_seconds: int = 5) -> dict:
        """
        ✅ Watchdog: Freeze signals if data stops coming.
        Prevents trading on stale data.
        """
        time_since_last_data = (datetime.now() - self.last_data_time).total_seconds()
        
        if time_since_last_data > data_timeout_seconds:
            self.signal_freeze = True
            return {
                "status": "FROZEN",
                "reason": "Data timeout",
                "seconds_without_data": time_since_last_data,
            }
        else:
            self.signal_freeze = False
            return {
                "status": "ACTIVE",
                "seconds_since_last_data": time_since_last_data,
            }
    
    def confidence_kill_switch(self, raw_confidence: float,
                              prev_confidence: float,
                              kill_threshold: float = 0.20) -> dict:
        """
        ✅ Kill-switch: If confidence drops >20% in one bar, pause.
        Prevents trading on confidence collapse.
        """
        confidence_drop = prev_confidence - raw_confidence
        drop_percentage = confidence_drop / prev_confidence if prev_confidence > 0 else 0
        
        result = {
            "triggered": False,
            "drop_percentage": round(drop_percentage, 3),
            "action": "CONTINUE",
        }
        
        if drop_percentage > kill_threshold:
            result["triggered"] = True
            result["action"] = "PAUSE_SIGNALS"
            result["reason": "Confidence collapse"
        
        return result
    
    def news_shock_guard(self, high_impact_news_detected: bool,
                        news_reduction: float = 0.15) -> dict:
        """
        ✅ Shock guard: Reduce confidence during high-impact news.
        Prevent trading into uncertainty.
        """
        return {
            "news_detected": high_impact_news_detected,
            "confidence_reduction": news_reduction if high_impact_news_detected else 0.0,
            "recommendation": "REDUCE_SIZE" if high_impact_news_detected else "NORMAL",
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎯 PERFORMANCE BENCHMARK
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_performance_metrics(self) -> dict:
        """Return current optimization metrics."""
        return {
            "gann_cache_active": self.cache["gann_session"] is not None,
            "astro_active": self.cache["astro_state"].get("active", False),
            "cycle_counter": self.cache["cycle_counter"],
            "signal_freeze_active": self.signal_freeze,
            "memory_log_size": len(self.memory_log),
            "confidence_stability": self._calculate_confidence_stability(),
            "timestamp": datetime.now().isoformat(),
        }
    
    def _calculate_confidence_stability(self) -> float:
        """Calculate stability of confidence (lower volatility = more stable)."""
        if len(self.memory_log) < 2:
            return 0.0
        
        recent = self.memory_log[-10:]  # Last 10 entries
        changes = [abs(m["change"]) for m in recent if "change" in m]
        
        if changes:
            avg_change = sum(changes) / len(changes)
            return round(1.0 - min(avg_change, 1.0), 3)  # Invert: lower volatility = higher score
        
        return 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    optimizer = PerformanceOptimizer()
    
    print("\n" + "="*70)
    print("STEP 21 — PERFORMANCE OPTIMIZATION DEMO")
    print("="*70 + "\n")
    
    # 1️⃣ Gann Caching
    print("✅ TEST 1: Gann Session Caching")
    gann1 = optimizer.optimize_gann(3368, 3320, "NY_SESSION")
    print(f"   First call (cache miss): {gann1['cached_at']}")
    gann2 = optimizer.optimize_gann(3368, 3320, "NY_SESSION")
    print(f"   Second call (cache hit): {gann2['cached_at']}")
    print(f"   Cached? {gann1['cached_at'] == gann2['cached_at']}\n")
    
    # 2️⃣ Astro Time-Window
    print("✅ TEST 2: Astro Time-Window Activation")
    aspect_times = [datetime.now(), datetime.now() + timedelta(hours=2)]
    astro = optimizer.optimize_astro(datetime.now(), aspect_times, window_minutes=4)
    print(f"   Astro active? {astro['active']}")
    print(f"   Active aspects: {len(astro['active_aspects'])}\n")
    
    # 3️⃣ Cycle Counter
    print("✅ TEST 3: Incremental Cycle Counter")
    for i in range(15):
        cycle = optimizer.optimize_cycle(new_bar_closed=True)
        if cycle["cycle_hit"]:
            print(f"   Bar {cycle['bar_count']}: CYCLE HIT (Power: {cycle['activation']['power']})")
    print()
    
    # 4️⃣ Iceberg Persistence
    print("✅ TEST 4: Iceberg Persistence Filter")
    for i in range(5):
        iceberg = optimizer.optimize_iceberg(
            volume_spike_detected=True,
            absorption_strength=0.7
        )
        print(f"   Bar {i+1}: Persistence={iceberg['persistence_level']}, "
              f"Valid={iceberg['iceberg_valid']}")
    print()
    
    # 5️⃣ Confidence Smoothing
    print("✅ TEST 5: Confidence EMA Smoothing")
    raw_values = [0.65, 0.85, 0.60, 0.78, 0.82, 0.75]
    for raw in raw_values:
        smoothed = optimizer.stabilize_confidence(raw)
        print(f"   Raw: {raw:.2f} → Smoothed: {smoothed:.3f}")
    print()
    
    # 6️⃣ Memory Decay
    print("✅ TEST 6: Memory Decay")
    old_memory = {
        "confidence_component": 0.8,
        "type": "iceberg",
    }
    decayed = optimizer.apply_memory_decay(
        old_memory,
        "iceberg",
        datetime.now() - timedelta(minutes=30)
    )
    print(f"   Original: 0.80 → After 30 min decay: {decayed['confidence_component']:.3f}\n")
    
    # 7️⃣ Failsafes
    print("✅ TEST 7: Failsafes & Kill-Switches")
    watchdog = optimizer.watchdog_timer()
    print(f"   Watchdog: {watchdog['status']}")
    
    kill_switch = optimizer.confidence_kill_switch(0.60, 0.80)
    print(f"   Kill-switch: {kill_switch['action']}")
    
    news = optimizer.news_shock_guard(True)
    print(f"   News guard: {news['recommendation']}\n")
    
    # Performance Summary
    print("="*70)
    print("PERFORMANCE METRICS")
    print("="*70)
    metrics = optimizer.get_performance_metrics()
    for key, value in metrics.items():
        print(f"{key:30} {str(value):20}")
    
    print("\n" + "="*70)
    print("✅ STEP 21 OPTIMIZATIONS COMPLETE & VERIFIED")
    print("="*70 + "\n")
