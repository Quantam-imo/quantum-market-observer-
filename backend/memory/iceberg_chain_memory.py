class IcebergChainMemory:
    def __init__(self):
        self.chains = []

    def add_to_chain(self, zone):
        for chain in self.chains:
            if self._overlaps(chain["zone"], zone):
                chain["occurrences"] += 1
                chain["sessions"].add(zone["session"])
                chain["last_seen"] = zone["timestamp"]
                return chain

        # create new chain
        self.chains.append({
            "zone": (zone["low"], zone["high"]),
            "side": zone["side"],
            "occurrences": 1,
            "sessions": {zone["session"]},
            "last_seen": zone["timestamp"]
        })

    def _overlaps(self, chain_zone, new_zone, tolerance=2):
        low1, high1 = chain_zone
        low2, high2 = new_zone["low"], new_zone["high"]
        return abs(low1 - low2) <= tolerance and abs(high1 - high2) <= tolerance
