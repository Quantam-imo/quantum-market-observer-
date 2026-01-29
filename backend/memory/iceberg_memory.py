import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class IcebergMemoryEngine:
    FILE = "iceberg_memory.json"

    def __init__(self) -> None:
        self.zones: List[Dict[str, Any]] = []
        self.load()

    # Basic persistence
    def save_zone(self, zone: Dict[str, Any]) -> None:
        self.zones.append(zone)
        self.save()

    def save(self) -> None:
        with open(self.FILE, "w") as f:
            json.dump(self.zones, f, indent=2)

    def load(self) -> None:
        if os.path.exists(self.FILE):
            with open(self.FILE, "r") as f:
                try:
                    self.zones = json.load(f)
                except Exception:
                    self.zones = []
        else:
            self.zones = []

    # Convenience API expected by pipeline/tests
    def store(self, zone: Dict[str, Any]) -> None:
        """Store a new iceberg/memory zone (absorption or sweep)."""
        # Normalize minimal fields
        if "times_retested" not in zone:
            zone["times_retested"] = 0
        if "date" not in zone:
            zone["date"] = datetime.utcnow().strftime("%Y-%m-%d")
        self.save_zone(zone)

    def record_iceberg(
        self,
        instrument: str,
        price_low: float,
        price_high: float,
        session: Optional[str],
        side: str,
        volume_strength: float,
        delta_bias: float,
        reaction_result: str,
    ) -> None:
        zone = {
            "instrument": instrument,
            "price_low": price_low,
            "price_high": price_high,
            "session": session,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "side": side,
            "volume_strength": volume_strength,
            "delta_bias": delta_bias,
            "reaction_result": reaction_result,
            "times_retested": 0,
        }
        self.save_zone(zone)

    def retest_zone(self, price: float, tolerance: float = 0.5) -> None:
        for zone in self.zones:
            low = zone.get("price_low")
            high = zone.get("price_high")
            level = zone.get("price")
            in_range = False
            if low is not None and high is not None:
                in_range = (low - tolerance) <= price <= (high + tolerance)
            elif level is not None:
                in_range = abs(level - price) <= tolerance
            if in_range:
                zone["times_retested"] = int(zone.get("times_retested", 0)) + 1
        self.save()

    def get_active_zones(
        self,
        price: Optional[float] = None,
        tolerance: float = 0.0,
        session: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        zones = [
            z
            for z in self.zones
            if (session is None or z.get("session") == session)
            and (z.get("date", today) <= today)
        ]
        if price is not None and tolerance > 0:
            filtered: List[Dict[str, Any]] = []
            for z in zones:
                low = z.get("price_low")
                high = z.get("price_high")
                level = z.get("price")
                if low is not None and high is not None:
                    if (low - tolerance) <= price <= (high + tolerance):
                        filtered.append(z)
                elif level is not None:
                    if abs(level - price) <= tolerance:
                        filtered.append(z)
            zones = filtered
        return zones

    def get_zones_for_chart(self) -> List[Dict[str, Any]]:
        # For chart overlays: return all zones with price/session/side
        return [
            {
                "price_low": z.get("price_low"),
                "price_high": z.get("price_high"),
                "session": z.get("session"),
                "side": z.get("side"),
                "date": z.get("date"),
                "times_retested": z.get("times_retested", 0),
            }
            for z in self.zones
        ]

    def clear_old_zones(self, days: int = 10) -> None:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        today_dt = datetime.strptime(today_str, "%Y-%m-%d")
        kept: List[Dict[str, Any]] = []
        for z in self.zones:
            date_str = z.get("date")
            if not date_str:
                kept.append(z)
                continue
            try:
                z_dt = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                kept.append(z)
                continue
            delta_days = (today_dt - z_dt).days
            if delta_days <= days:
                kept.append(z)
        self.zones = kept
        self.save()

    def summary(self) -> Dict[str, Any]:
        """Return a summary of memory zones for dashboard."""
        total_zones = len(self.zones)
        strong_zones = len([z for z in self.zones if z.get("times_retested", 0) >= 2])
        return {
            "total_zones_stored": total_zones,
            "strong_zones": strong_zones,
        }

    def get_strong_zones(self, min_reuse: int = 1) -> List[Dict[str, Any]]:
        """Return zones with at least min_reuse retests."""
        return [z for z in self.zones if z.get("times_retested", 0) >= min_reuse]
