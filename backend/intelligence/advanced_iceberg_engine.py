"""
Iceberg Detection Engine - Infers institutional iceberg orders from market behavior
NOT a direct feed, but sophisticated proxy detection from CME GC data
"""

from typing import Dict, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class IcebergDetector:
    """
    Detects probable iceberg order absorption zones.
    
    Institutional iceberg detection rules (no direct CME labels):
    
    ABSORPTION BUY SIGNATURE:
    - Price declining steadily
    - Sudden large volume prints
    - Volume absorbs downside momentum
    - Delta stays negative (selling pressure absorbed)
    - Price stabilizes after absorption
    
    ABSORPTION SELL SIGNATURE:
    - Price rallying
    - Heavy volume at resistance
    - Wicks fail above key levels
    - Delta turns positive (but can't break higher)
    - Repeated rejection at same price
    """
    
    def __init__(self):
        self.absorption_zones = {}  # price -> {volume, count, direction}
        self.volume_threshold = 50  # Contracts (lowered for faster detection)
        self.price_bucket = 0.5  # Round to nearest 0.5
        self.history = []  # Track all detections
        self.last_detection_time = None  # Track last detection for real-time updates
        
    def detect_absorption_zones(self, trades: List[Dict]) -> List[Dict]:
        """
        Scan trades for absorption signatures.
        
        Input: List of trades {price, size, side, timestamp}
        Output: List of absorption zones detected
        """
        absorption_zones = []
        
        if not trades or len(trades) < 10:
            return absorption_zones
        
        # Bucket trades by price level
        price_buckets = defaultdict(int)
        for trade in trades:
            price_key = round(trade["price"] / self.price_bucket) * self.price_bucket
            price_buckets[price_key] += trade["size"]
        
        # Find abnormal volume clusters
        avg_volume = sum(price_buckets.values()) / len(price_buckets) if price_buckets else 0
        
        for price, volume in price_buckets.items():
            # Volume > 1.5x average = potential absorption (more sensitive)
            if volume > max(self.volume_threshold, avg_volume * 1.5):
                
                # Determine direction by analyzing nearby trades
                direction = self._infer_direction(trades, price)
                
                zone = {
                    "price": price,
                    "volume": volume,
                    "direction": direction,
                    "confidence": self._calculate_confidence(volume, avg_volume),
                    "type": "ICEBERG_ABSORPTION"
                }
                
                absorption_zones.append(zone)
                self._record_zone(zone)
        
        return absorption_zones
    
    def _infer_direction(self, trades: List[Dict], price: float) -> str:
        """
        Infer if iceberg is BUY-side or SELL-side.
        
        Logic:
        - BUY-side: Large volume at support, stops downside
        - SELL-side: Heavy volume at resistance, stops upside
        """
        # Trades near this price
        near_trades = [t for t in trades if abs(t["price"] - price) < 1.0]
        
        if not near_trades:
            return "UNKNOWN"
        
        # Count buys vs sells
        buys = sum(t["size"] for t in near_trades if t["side"] == "BUY")
        sells = sum(t["size"] for t in near_trades if t["side"] == "SELL")
        
        if buys > sells * 1.5:
            return "BUY_SIDE"
        elif sells > buys * 1.5:
            return "SELL_SIDE"
        else:
            return "NEUTRAL"
    
    def _calculate_confidence(self, volume: float, avg_volume: float) -> float:
        """
        Confidence score 0.0-1.0 for iceberg detection.
        
        More volume >> higher confidence
        """
        if avg_volume == 0:
            return 0.5
        
        ratio = volume / avg_volume
        
        # Scaling: 3x avg = 60%, 5x avg = 85%, 10x avg = 95%
        confidence = min(0.95, 0.3 + (ratio - 3) * 0.15)
        return max(0.3, confidence)
    
    def detect_sweep_probability(self, 
                                 price: float, 
                                 bid: float, 
                                 ask: float,
                                 bid_volume: int,
                                 ask_volume: int) -> float:
        """
        Probability that liquidity will be swept at this level.
        
        Higher when:
        - Price near key levels
        - Imbalance in bid/ask volume
        - Multiple absorption zones above/below
        """
        if bid == 0 or ask == 0:
            return 0.0
        
        # Bid/ask imbalance
        if bid_volume > 0:
            imbalance = abs(ask_volume - bid_volume) / (bid_volume + ask_volume)
        else:
            imbalance = 0.5
        
        # Proximity to absorption zones
        proximity_score = self._proximity_to_zones(price)
        
        # Combined probability
        sweep_prob = (imbalance * 0.6) + (proximity_score * 0.4)
        
        return min(1.0, sweep_prob)
    
    def _proximity_to_zones(self, price: float) -> float:
        """Score: how close is price to known absorption zones?"""
        if not self.absorption_zones:
            return 0.0
        
        distances = [abs(price - zone_price) for zone_price in self.absorption_zones.keys()]
        
        if not distances:
            return 0.0
        
        min_distance = min(distances)
        
        # Closer to zone = higher score
        return max(0.0, 1.0 - (min_distance / 10.0))
    
    def detect_absorption_pair(self, 
                               trades: List[Dict],
                               structure: Dict) -> Optional[Dict]:
        """
        Detect BUY and SELL absorption zones as institutional pair.
        
        Typical pattern:
        - Seller creates downside absorption (BUY-side iceberg holds)
        - Buyer creates upside absorption (SELL-side iceberg holds)
        - Price oscillates between them
        
        Returns: {buy_level, sell_level, range, efficiency}
        """
        zones = self.detect_absorption_zones(trades)
        
        buy_zones = [z for z in zones if z["direction"] == "BUY_SIDE"]
        sell_zones = [z for z in zones if z["direction"] == "SELL_SIDE"]
        
        if not buy_zones or not sell_zones:
            return None
        
        # Get strongest zones
        buy_zone = max(buy_zones, key=lambda z: z["confidence"])
        sell_zone = max(sell_zones, key=lambda z: z["confidence"])
        
        if buy_zone["price"] >= sell_zone["price"]:
            # Invalid pair
            return None
        
        pair = {
            "buy_level": buy_zone["price"],
            "buy_volume": buy_zone["volume"],
            "buy_confidence": buy_zone["confidence"],
            "sell_level": sell_zone["price"],
            "sell_volume": sell_zone["volume"],
            "sell_confidence": sell_zone["confidence"],
            "range": sell_zone["price"] - buy_zone["price"],
            "efficiency": self._calculate_efficiency(buy_zone, sell_zone),
            "type": "INSTITUTIONAL_PAIR"
        }
        
        return pair
    
    def _calculate_efficiency(self, buy_zone: Dict, sell_zone: Dict) -> float:
        """
        Efficiency: How well do zones control price?
        
        Range efficiency = (abs range) / (avg volume)
        Higher = better control
        """
        range_size = sell_zone["price"] - buy_zone["price"]
        avg_volume = (buy_zone["volume"] + sell_zone["volume"]) / 2
        
        if avg_volume == 0:
            return 0.0
        
        efficiency = range_size / avg_volume
        
        # Normalize to 0-1
        return min(1.0, efficiency / 0.1)  # 0.1 is reference efficiency
    
    def _record_zone(self, zone: Dict):
        """Record absorption zone for future reference."""
        price = zone["price"]
        
        if price not in self.absorption_zones:
            self.absorption_zones[price] = {
                "volume": 0,
                "count": 0,
                "direction": zone["direction"],
                "last_seen": None
            }
        
        self.absorption_zones[price]["volume"] += zone["volume"]
        self.absorption_zones[price]["count"] += 1
        self.absorption_zones[price]["last_seen"] = zone.get("timestamp")
    
    def get_active_zones(self, time_window_minutes: int = 60) -> Dict:
        """
        Get recently active absorption zones.
        
        Returns zones that appeared in last N minutes.
        """
        # In production, filter by timestamp
        # For now, return all tracked zones
        return self.absorption_zones
    
    def estimate_institutional_activity(self, ohlc: Dict) -> float:
        """
        Estimate institutional activity level 0.0-1.0.
        
        High when:
        - Multiple absorption zones detected
        - Large volume swings
        - Wide range on small tick count
        """
        if "range" not in ohlc or "volume" not in ohlc:
            return 0.5
        
        zone_count = len(self.absorption_zones)
        
        # Normalized factors
        zone_factor = min(1.0, zone_count / 5.0)  # 5+ zones = max
        volume_factor = min(1.0, ohlc["volume"] / 10000)  # 10k+ volume
        range_factor = min(1.0, ohlc["range"] / 50)  # 50+ point range
        
        # Combined score
        activity = (zone_factor * 0.4) + (volume_factor * 0.3) + (range_factor * 0.3)
        
        return activity


class AbsorptionZoneMemory:
    """
    Maintains session history of absorption zones.
    Tracks zone effectiveness and evolution.
    """
    
    def __init__(self):
        self.zones = []  # Historical zones
        self.max_history = 100
        
    def record(self, zone: Dict):
        """Record a detected zone."""
        self.zones.append({
            **zone,
            "timestamp": zone.get("timestamp")
        })
        
        # Keep only recent history
        if len(self.zones) > self.max_history:
            self.zones.pop(0)
    
    def get_zone_clusters(self, tolerance: float = 2.0) -> List[Dict]:
        """
        Group nearby zones into clusters.
        Tolerance: maximum distance to group zones.
        """
        if not self.zones:
            return []
        
        clusters = []
        sorted_zones = sorted(self.zones, key=lambda z: z["price"])
        
        current_cluster = [sorted_zones[0]]
        
        for zone in sorted_zones[1:]:
            if zone["price"] - current_cluster[-1]["price"] <= tolerance:
                current_cluster.append(zone)
            else:
                clusters.append(self._cluster_stats(current_cluster))
                current_cluster = [zone]
        
        if current_cluster:
            clusters.append(self._cluster_stats(current_cluster))
        
        return clusters
    
    def _cluster_stats(self, cluster: List[Dict]) -> Dict:
        """Compute statistics for a zone cluster."""
        prices = [z["price"] for z in cluster]
        volumes = [z["volume"] for z in cluster]
        
        return {
            "center_price": sum(prices) / len(prices),
            "price_range": max(prices) - min(prices),
            "total_volume": sum(volumes),
            "zone_count": len(cluster),
            "avg_confidence": sum(z["confidence"] for z in cluster) / len(cluster)
        }
