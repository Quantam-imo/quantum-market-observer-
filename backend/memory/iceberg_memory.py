
from datetime import datetime

class IcebergMemory:
    def __init__(self):
        self.zones = []
        self.levels = []  # For price-level memory

    def record_zone(self, zone):
        self.zones.append({
            "id": len(self.zones) + 1,
            "price_low": zone["low"],
            "price_high": zone["high"],
            "side": zone["side"],  # BUY or SELL
            "session": zone["session"],
            "timestamp": datetime.utcnow(),
            "outcome": None,
            "score": 0.0
        })

    def store(self, price_from, price_to, side, session):
        self.levels.append({
            "from": price_from,
            "to": price_to,
            "side": side,
            "session": session
        })

    def update_outcome(self, zone_id, outcome):
        for z in self.zones:
            if z["id"] == zone_id:
                z["outcome"] = outcome
                z["score"] += 1 if outcome == "SUCCESS" else -1
