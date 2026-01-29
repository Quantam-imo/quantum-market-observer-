import json
from datetime import datetime
from pathlib import Path

class IcebergEngine:
    def __init__(self, memory_file="iceberg_memory.json"):
        self.active_zones = []
        self.memory_file = Path(memory_file)
        self.memory = self._load_memory()
        
    def _load_memory(self):
        """Load historical iceberg performance from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"zones": [], "stats": {"total": 0, "successful": 0, "failed": 0}}
    
    def _save_memory(self):
        """Persist iceberg memory to disk"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def detect_sell_iceberg(self, candles):
        """Detect sell-side iceberg absorption (rejection wicks)"""
        rejections = 0
        for c in candles[-6:]:
            body = abs(c["close"] - c["open"])
            wick = c["high"] - max(c["open"], c["close"])
            if wick > body:
                rejections += 1
        return rejections >= 3
    
    def detect_buy_iceberg(self, candles):
        """Detect buy-side iceberg absorption (lower wick rejection)"""
        rejections = 0
        for c in candles[-6:]:
            body = abs(c["close"] - c["open"])
            wick = min(c["open"], c["close"]) - c["low"]
            if wick > body:
                rejections += 1
        return rejections >= 3
    
    def find_absorption_zones(self, candles, lookback=20):
        """Find price zones with high volume absorption"""
        if len(candles) < lookback:
            return []
        
        recent = candles[-lookback:]
        avg_volume = sum(c["volume"] for c in recent) / len(recent)
        
        zones = []
        for i, candle in enumerate(recent):
            if candle["volume"] > avg_volume * 1.5:  # 50% above average
                zone_price = (candle["high"] + candle["low"]) / 2
                
                # Check if we've seen this zone before
                historical_data = self._get_zone_history(zone_price)
                success_rate = historical_data["success_rate"] if historical_data else 0.5
                
                zones.append({
                    "price": zone_price,
                    "price_top": candle["high"],
                    "price_bottom": candle["low"],
                    "volume": candle["volume"],
                    "timestamp": candle.get("timestamp", ""),
                    "success_rate": success_rate,
                    "trades": historical_data["trades"] if historical_data else 0,
                    "bias": "BUY" if candle["close"] > candle["open"] else "SELL"
                })
        
        return zones
    
    def _get_zone_history(self, price, tolerance=10.0):
        """Get historical performance of a price zone"""
        for zone in self.memory["zones"]:
            if abs(zone["price"] - price) < tolerance:
                total = zone["wins"] + zone["losses"]
                return {
                    "success_rate": zone["wins"] / total if total > 0 else 0.5,
                    "trades": total,
                    "wins": zone["wins"],
                    "losses": zone["losses"]
                }
        return None
    
    def record_zone_outcome(self, price, success: bool):
        """Record outcome of trading an iceberg zone"""
        found = False
        for zone in self.memory["zones"]:
            if abs(zone["price"] - price) < 10.0:
                if success:
                    zone["wins"] += 1
                    self.memory["stats"]["successful"] += 1
                else:
                    zone["losses"] += 1
                    self.memory["stats"]["failed"] += 1
                zone["last_seen"] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            self.memory["zones"].append({
                "price": price,
                "wins": 1 if success else 0,
                "losses": 0 if success else 1,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            })
        
        self.memory["stats"]["total"] += 1
        self._save_memory()
    
    def get_best_zones(self, top_n=5):
        """Get top N performing iceberg zones by win rate"""
        zones = [z for z in self.memory["zones"] if z["wins"] + z["losses"] >= 3]
        zones.sort(key=lambda z: z["wins"] / (z["wins"] + z["losses"]), reverse=True)
        return zones[:top_n]
