import math
import time

class AstroEngine:
    def moon_degree(self):
        return (time.time() / 86400 * 13) % 360

    def is_reversal_window(self):
        deg = self.moon_degree()
        return abs(deg % 90) < 3
