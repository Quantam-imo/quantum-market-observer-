class IcebergEngine:
    def detect(self, volume, delta):
        return volume > 3 and delta < 0
