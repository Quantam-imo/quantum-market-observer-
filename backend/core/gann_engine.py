import math

class GannEngine:
    """
    Advanced Gann Analysis Engine
    Implements Gann Square of 9, Gann Angles, and Price-Time projections
    """
    
    # Traditional Gann multipliers
    multipliers = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 6, 8]
    
    # Gann angles (price/time ratios)
    gann_angles = {
        "1x8": 1/8, "1x4": 1/4, "1x3": 1/3, "1x2": 1/2,
        "1x1": 1,  # 45-degree angle - most important
        "2x1": 2, "3x1": 3, "4x1": 4, "8x1": 8
    }

    def levels(self, high, low):
        """Calculate Gann extension/retracement levels"""
        base = abs(high - low)
        levels = {}
        for m in self.multipliers:
            pct = int(m * 100)
            levels[f"{pct}%"] = {
                "extension": round(high + base * m, 2),
                "retracement": round(high - base * m, 2),
                "from_low": round(low + base * m, 2)
            }
        return levels
    
    def square_of_nine(self, price, rotations=4):
        """
        Gann Square of 9 - Projects support/resistance levels
        Price sits at center, rotations create spiral of key levels
        """
        sqrt_price = math.sqrt(price)
        levels = {"base": price, "supports": [], "resistances": []}
        
        for i in range(1, rotations + 1):
            # Resistance (add rotations)
            resist = (sqrt_price + i * 0.25) ** 2
            levels["resistances"].append(round(resist, 2))
            
            # Support (subtract rotations)
            if sqrt_price - i * 0.25 > 0:
                support = (sqrt_price - i * 0.25) ** 2
                levels["supports"].append(round(support, 2))
        
        return levels
    
    def calculate_angles(self, price, range_size, time_units=10):
        """
        Calculate Gann angle lines from a pivot price
        Returns price projections at future time units
        """
        angles = {}
        for name, slope in self.gann_angles.items():
            # Project price movement along Gann angle
            up_projection = price + (slope * range_size * time_units)
            down_projection = price - (slope * range_size * time_units)
            angles[name] = {
                "uptrend": round(up_projection, 2),
                "downtrend": round(down_projection, 2),
                "slope": slope
            }
        return angles
    
    def time_cycles(self, pivot_date, natural_cycles=True):
        """
        Gann time cycles - Key reversal time points
        Natural cycles: 7, 30, 60, 90, 120, 144, 180, 360 days
        """
        if natural_cycles:
            cycles = [7, 30, 60, 90, 120, 144, 180, 360]
        else:
            # Fibonacci-based cycles
            cycles = [8, 13, 21, 34, 55, 89, 144, 233]
        
        return {f"T+{c}": c for c in cycles}
    
    def cardinal_cross(self, price):
        """
        Gann Cardinal Cross - 0°, 90°, 180°, 270° on Square of 9
        These are strongest support/resistance levels
        """
        sqrt_price = math.sqrt(price)
        
        # Cardinal points (every 90° or 0.25 rotation)
        levels = []
        for angle in [0, 90, 180, 270]:
            rotation = angle / 360  # Convert to rotation units
            cardinal_price = (sqrt_price + rotation) ** 2
            levels.append({
                "angle": angle,
                "price": round(cardinal_price, 2),
                "strength": "CRITICAL" if angle in [0, 180] else "STRONG"
            })
        
        return levels
    
    def price_clusters(self, current_price, high, low):
        """
        Find Gann price clusters where multiple levels converge
        These are high-probability reversal zones
        """
        all_levels = []
        
        # Get extension levels
        extensions = self.levels(high, low)
        for key, vals in extensions.items():
            all_levels.extend([vals["extension"], vals["retracement"], vals["from_low"]])
        
        # Get Square of 9 levels
        sq9 = self.square_of_nine(current_price)
        all_levels.extend(sq9["supports"] + sq9["resistances"])
        
        # Find clusters (levels within 1% of each other)
        clusters = []
        tolerance = current_price * 0.01
        
        for level in all_levels:
            nearby = [l for l in all_levels if abs(l - level) < tolerance]
            if len(nearby) >= 3:  # At least 3 levels converge
                cluster_price = sum(nearby) / len(nearby)
                if not any(abs(c["price"] - cluster_price) < tolerance for c in clusters):
                    clusters.append({
                        "price": round(cluster_price, 2),
                        "confluence": len(nearby),
                        "strength": "VERY STRONG" if len(nearby) >= 5 else "STRONG"
                    })
        
        return sorted(clusters, key=lambda x: x["confluence"], reverse=True)
