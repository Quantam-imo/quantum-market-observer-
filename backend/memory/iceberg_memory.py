class IcebergMemory:
    """Maintains history of detected iceberg orders."""
    
    def __init__(self):
        self.icebergs = []

    def add_iceberg(self, volume, level, timestamp):
        """Record detected iceberg order."""
        self.icebergs.append({"volume": volume, "level": level, "timestamp": timestamp})

    def get_recent(self, bars=50):
        """Retrieve recent iceberg activity."""
        return self.icebergs[-bars:] if len(self.icebergs) > 0 else []
