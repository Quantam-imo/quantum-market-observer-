class CycleMemory:
    """Stores identified cycle patterns and timings."""
    
    def __init__(self):
        self.cycles = {}

    def record_cycle(self, cycle_type, start_bar, end_bar):
        """Store detected cycle."""
        key = f"{cycle_type}_{start_bar}"
        self.cycles[key] = {"type": cycle_type, "start": start_bar, "end": end_bar}

    def active_cycles(self, current_bar):
        """Get cycles still in effect at current bar."""
        return {k: v for k, v in self.cycles.items() if v["end"] > current_bar}
