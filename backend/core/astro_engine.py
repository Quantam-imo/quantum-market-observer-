"""
Advanced Astrological Market Analysis Engine
Implements planetary aspects, retrogrades, and market correlations
Based on W.D. Gann's astrological market forecasting techniques
"""

from datetime import datetime, timedelta
import math

class AstroEngine:
    """
    Financial Astrology Engine
    Analyzes planetary aspects and their correlation with market movements
    """
    
    # Major aspects (Ptolemaic aspects)
    major_aspects = {
        "conjunction": 0,      # 0° - Very strong, new cycle
        "sextile": 60,         # 60° - Opportunity, mild positive
        "square": 90,          # 90° - Tension, volatility
        "trine": 120,          # 120° - Harmony, trend continuation
        "opposition": 180      # 180° - Conflict, reversal potential
    }
    
    # Minor aspects (used by advanced traders)
    minor_aspects = {
        "semi-sextile": 30,
        "semi-square": 45,
        "sesquiquadrate": 135,
        "quincunx": 150
    }
    
    # Planet speeds (degrees per day - approximate)
    planet_speeds = {
        "Sun": 1.0,
        "Moon": 13.2,
        "Mercury": 1.6,
        "Venus": 1.2,
        "Mars": 0.5,
        "Jupiter": 0.08,
        "Saturn": 0.03,
        "Uranus": 0.01,
        "Neptune": 0.006,
        "Pluto": 0.004
    }
    
    # Market correlation strength
    market_influence = {
        "Sun": 0.3,      # General trend
        "Moon": 0.4,     # Short-term volatility
        "Mercury": 0.5,  # Communication, data
        "Venus": 0.2,    # Risk appetite
        "Mars": 0.6,     # Energy, volatility
        "Jupiter": 0.7,  # Expansion, bull markets
        "Saturn": 0.8,   # Contraction, bear markets
        "Uranus": 0.5,   # Sudden changes, shocks
        "Neptune": 0.3,  # Confusion, bubbles
        "Pluto": 0.4     # Transformation, major shifts
    }

    def aspect(self, d1, d2):
        """Calculate aspect angle between two planetary positions"""
        diff = abs(d1 - d2) % 360
        return min(diff, 360 - diff)

    def is_major(self, d1, d2, orb=1):
        """Check if aspect is major (within orb tolerance)"""
        angle = self.aspect(d1, d2)
        return any(abs(angle - a) <= orb for a in self.major_aspects.values())
    
    def identify_aspect(self, angle, orb=2):
        """Identify the type of aspect from angle"""
        # Check major aspects first
        for name, degree in self.major_aspects.items():
            if abs(angle - degree) <= orb:
                return {
                    "type": name,
                    "category": "major",
                    "exact_angle": degree,
                    "actual_angle": angle,
                    "orb": abs(angle - degree)
                }
        
        # Check minor aspects
        for name, degree in self.minor_aspects.items():
            if abs(angle - degree) <= orb:
                return {
                    "type": name,
                    "category": "minor",
                    "exact_angle": degree,
                    "actual_angle": angle,
                    "orb": abs(angle - degree)
                }
        
        return None
    
    def get_planet_position(self, planet, date=None):
        """
        Get approximate planetary position for given date
        Simplified calculation - real implementation would use ephemeris
        """
        if date is None:
            date = datetime.utcnow()
        
        # Reference date (Jan 1, 2026)
        ref_date = datetime(2026, 1, 1)
        days_diff = (date - ref_date).days
        
        # Base positions at reference date (example values)
        base_positions = {
            "Sun": 280,
            "Moon": 45,
            "Mercury": 295,
            "Venus": 315,
            "Mars": 90,
            "Jupiter": 30,
            "Saturn": 350,
            "Uranus": 25,
            "Neptune": 355,
            "Pluto": 0
        }
        
        if planet not in base_positions:
            return None
        
        # Calculate current position
        speed = self.planet_speeds.get(planet, 0)
        position = (base_positions[planet] + (speed * days_diff)) % 360
        
        return round(position, 2)
    
    def calculate_aspects_now(self, planets=None):
        """
        Calculate all current planetary aspects
        Returns list of active aspects with market implications
        """
        if planets is None:
            planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        
        aspects = []
        positions = {p: self.get_planet_position(p) for p in planets}
        
        # Check all planet pairs
        for i, planet1 in enumerate(planets):
            for planet2 in planets[i+1:]:
                pos1 = positions[planet1]
                pos2 = positions[planet2]
                
                if pos1 is None or pos2 is None:
                    continue
                
                angle = self.aspect(pos1, pos2)
                aspect_info = self.identify_aspect(angle)
                
                if aspect_info:
                    # Calculate market impact
                    influence = (self.market_influence[planet1] + self.market_influence[planet2]) / 2
                    
                    # Calculate timing information for aspect
                    current_time = datetime.utcnow()
                    
                    # Estimate when aspect became exact (based on orb)
                    # Faster planet determines timing
                    speed1 = self.planet_speeds[planet1]
                    speed2 = self.planet_speeds[planet2]
                    faster_speed = max(speed1, speed2)
                    
                    # Days since exact aspect (orb / faster_speed)
                    days_since_exact = aspect_info["orb"] / faster_speed if faster_speed > 0 else 0
                    exact_time = current_time - timedelta(days=days_since_exact)
                    
                    # Aspect remains active for ~3 degrees of orb (approx duration)
                    orb_window = 3.0  # degrees
                    days_active = orb_window / faster_speed if faster_speed > 0 else 7
                    
                    start_time = exact_time - timedelta(days=days_active / 2)
                    end_time = exact_time + timedelta(days=days_active / 2)
                    
                    aspects.append({
                        "planet1": planet1,
                        "planet2": planet2,
                        "aspect": aspect_info["type"],
                        "category": aspect_info["category"],
                        "angle": angle,
                        "orb": aspect_info["orb"],
                        "market_influence": influence,
                        "interpretation": self._interpret_aspect(planet1, planet2, aspect_info["type"]),
                        "exact_date": exact_time.isoformat(),
                        "start_date": start_time.isoformat(),
                        "end_date": end_time.isoformat(),
                        "is_applying": aspect_info["orb"] > 0.5,  # Aspect is still building
                        "is_exact": aspect_info["orb"] < 0.5  # Aspect is exact/very close
                    })
        
        return sorted(aspects, key=lambda x: x["market_influence"], reverse=True)
    
    def _interpret_aspect(self, planet1, planet2, aspect_type):
        """Interpret aspect for market implications"""
        interpretations = {
            "conjunction": {
                "Mars-Jupiter": "Aggressive expansion, bullish energy",
                "Saturn-Pluto": "Major structural change, market transformation",
                "Sun-Mercury": "Clear communication, data-driven moves"
            },
            "square": {
                "Mars-Saturn": "High volatility, aggressive selling pressure",
                "Jupiter-Uranus": "Unexpected expansion, bubble risk",
                "Moon-Mars": "Emotional volatility, panic possible"
            },
            "opposition": {
                "Sun-Saturn": "Trend exhaustion, reversal likely",
                "Mars-Neptune": "Confusion, false breakouts",
                "Venus-Pluto": "Risk reassessment, capital flight"
            },
            "trine": {
                "Jupiter-Sun": "Strong uptrend, confidence high",
                "Venus-Jupiter": "Risk appetite strong, buy signal",
                "Moon-Sun": "Stable trends, good trading conditions"
            },
            "sextile": {
                "Mercury-Venus": "Good risk/reward setups",
                "Sun-Mars": "Momentum building, trend acceleration",
                "Moon-Mercury": "Short-term opportunities"
            }
        }
        
        pair = f"{planet1}-{planet2}"
        reverse_pair = f"{planet2}-{planet1}"
        
        if aspect_type in interpretations:
            return (interpretations[aspect_type].get(pair) or 
                   interpretations[aspect_type].get(reverse_pair) or
                   f"{aspect_type.title()} aspect - moderate market impact")
        
        return "Minor aspect - watch for confirmation"
    
    def get_market_forecast(self, days_ahead=7):
        """
        Forecast upcoming astrological events
        Returns list of significant aspects in next N days
        """
        forecast = []
        base_date = datetime.utcnow()
        
        for day in range(1, days_ahead + 1):
            future_date = base_date + timedelta(days=day)
            aspects = self.calculate_aspects_now()
            
            if aspects:
                forecast.append({
                    "date": future_date.strftime("%Y-%m-%d"),
                    "days_ahead": day,
                    "major_aspects": [a for a in aspects if a["category"] == "major"][:3]
                })
        
        return forecast
    
    def get_retrograde_status(self, planet):
        """
        Check if planet is retrograde
        Simplified - real implementation would check ephemeris
        """
        # Mercury retrograde roughly 3 times/year, 3 weeks each
        # This is a simplified simulation
        retrogrades = {
            "Mercury": [1, 5, 9],  # months with retrograde
            "Venus": [7],
            "Mars": [10, 11],
            "Jupiter": [4, 5],
            "Saturn": [6, 7, 8]
        }
        
        current_month = datetime.utcnow().month
        is_retrograde = current_month in retrogrades.get(planet, [])
        
        return {
            "planet": planet,
            "is_retrograde": is_retrograde,
            "market_impact": "Delays, reversals, review periods" if is_retrograde else "Normal forward motion"
        }
    
    def get_moon_phase(self):
        """Calculate current moon phase"""
        # Simplified calculation
        days_since_new = (datetime.utcnow() - datetime(2026, 1, 1)).days % 29.5
        phase_pct = (days_since_new / 29.5) * 100
        
        if phase_pct < 12.5:
            phase = "New Moon"
            impact = "New cycles begin, low volatility"
        elif phase_pct < 37.5:
            phase = "Waxing Crescent"
            impact = "Building momentum, bullish bias"
        elif phase_pct < 62.5:
            phase = "Full Moon"
            impact = "Peak volatility, major moves likely"
        elif phase_pct < 87.5:
            phase = "Waning Gibbous"
            impact = "Decreasing activity, profit-taking"
        else:
            phase = "Waning Crescent"
            impact = "Consolidation, prepare for new cycle"
        
        return {
            "phase": phase,
            "percentage": round(phase_pct, 1),
            "market_impact": impact
        }
    
    def get_trading_outlook(self):
        """
        Get overall astrological trading outlook
        Combines aspects, moon phase, and retrogrades
        """
        aspects = self.calculate_aspects_now()
        moon = self.get_moon_phase()
        mercury_rx = self.get_retrograde_status("Mercury")
        
        # Calculate overall score
        bullish_score = 0
        bearish_score = 0
        volatility_score = 0
        
        for aspect in aspects[:5]:  # Top 5 most influential
            influence = aspect["market_influence"]
            
            if aspect["aspect"] in ["trine", "sextile"]:
                bullish_score += influence
            elif aspect["aspect"] in ["square", "opposition"]:
                bearish_score += influence
                volatility_score += influence * 0.5
            elif aspect["aspect"] == "conjunction":
                volatility_score += influence * 0.3
        
        # Moon phase influence
        if "Full Moon" in moon["phase"]:
            volatility_score += 0.3
        
        # Mercury retrograde caution
        if mercury_rx["is_retrograde"]:
            volatility_score += 0.2
        
        # Determine outlook
        if bullish_score > bearish_score + 0.5:
            outlook = "BULLISH"
            confidence = min(85, int(bullish_score * 30))
        elif bearish_score > bullish_score + 0.5:
            outlook = "BEARISH"
            confidence = min(85, int(bearish_score * 30))
        else:
            outlook = "NEUTRAL"
            confidence = 50
        
        return {
            "outlook": outlook,
            "confidence": confidence,
            "volatility": "HIGH" if volatility_score > 1.5 else "MODERATE" if volatility_score > 0.8 else "LOW",
            "bullish_score": round(bullish_score, 2),
            "bearish_score": round(bearish_score, 2),
            "top_aspects": aspects[:3],
            "moon_phase": moon,
            "mercury_retrograde": mercury_rx["is_retrograde"]
        }

