"""
IMO Engine — The Institutional Market Observer Decision Framework
This is the execution filter: YES / NO / WAIT decisions based on market structure
"""

class IMOEngine:
    """
    IMO (Institutional Market Observer) evaluates whether structural conditions
    align with institutional participation and market conditions for execution.
    
    Output: CONFIDENCE SCORE (0.0 to 1.0) for mentor decision-making
    """
    
    def __init__(self):
        self.last_decision = None
        self.decision_history = []
    
    def evaluate(self, context):
        """
        Evaluate institutional market conditions.
        
        Args:
            context: Dictionary containing:
                - absorption_zones: List of detected absorption zones
                - sweeps: List of detected sweeps
                - current_price: Current market price
                - memory_forecast: Predicted zones from iceberg memory
                - trend: Current trend direction if available
        
        Returns:
            Dictionary with decision and confidence
        """
        score = 0.0
        reasons = []
        
        absorption_zones = context.get("absorption_zones", [])
        sweeps = context.get("sweeps", [])
        current_price = context.get("current_price", 0)
        memory_zones = context.get("memory_zones", [])
        volume = context.get("volume", 0)
        
        # ===== SCORING FRAMEWORK =====
        
        # 1. ABSORPTION QUALITY (0-0.3)
        absorption_score = 0.0
        if absorption_zones:
            strong_absorptions = [z for z in absorption_zones if z.get("strength", 0) > 0.6]
            if strong_absorptions:
                absorption_score = min(len(strong_absorptions) * 0.1, 0.3)
                reasons.append(f"Strong absorption detected ({len(strong_absorptions)} zones)")
            else:
                absorption_score = 0.1
                reasons.append("Weak absorption signal")
        score += absorption_score
        
        # 2. SWEEP CONFIRMATION (0-0.25)
        sweep_score = 0.0
        if sweeps:
            strong_sweeps = [s for s in sweeps if s.get("strength", 0) > 0.6]
            if strong_sweeps:
                sweep_score = min(len(strong_sweeps) * 0.1, 0.25)
                reasons.append(f"Liquidity sweeps detected ({len(strong_sweeps)} traps)")
            else:
                sweep_score = 0.05
        score += sweep_score
        
        # 3. MEMORY CONFLUENCE (0-0.2)
        memory_score = 0.0
        if memory_zones:
            active_memory = [z for z in memory_zones if abs(z.get("price", 0) - current_price) <= 3]
            if active_memory:
                reuse_counts = [z.get("reuse_count", 1) for z in active_memory]
                avg_reuse = sum(reuse_counts) / len(reuse_counts)
                if avg_reuse >= 2:
                    memory_score = 0.15
                    reasons.append(f"Multi-session zone confluence (avg reuse: {avg_reuse:.1f}x)")
                else:
                    memory_score = 0.08
                    reasons.append("Single-session zone, lower conviction")
        score += memory_score
        
        # 4. VOLUME CONFIRMATION (0-0.15)
        volume_score = 0.0
        if volume > 500:
            volume_score = min(volume / 2000, 0.15)
            reasons.append(f"Volume confirmation ({volume})")
        score += volume_score
        
        # 5. STRUCTURAL INTEGRITY (0-0.1)
        # Penalize if absorption and sweeps don't align
        integrity_score = 0.1  # Default positive for structure present
        if absorption_zones and sweeps:
            # Check if on same side (both buying or both selling)
            absorption_bias = "SELL" if any(z.get("dominance") == "SELL" for z in absorption_zones) else "BUY"
            sweep_type = sweeps[0].get("type", "")
            
            if (absorption_bias == "SELL" and "SELL" in sweep_type) or \
               (absorption_bias == "BUY" and "BUY" in sweep_type):
                integrity_score = 0.1
                reasons.append("Structural bias aligned")
            else:
                integrity_score = 0.0
                reasons.append("Structural conflict (absorption vs sweep bias)")
        score += integrity_score
        
        # ===== DECISION LOGIC =====
        
        confidence = min(score, 1.0)
        
        if confidence >= 0.7:
            decision = "EXECUTE"
            reason = "High institutional conviction"
        elif confidence >= 0.5:
            decision = "WAIT"
            reason = "Moderate signal, wait for confirmation"
        else:
            decision = "SKIP"
            reason = "Insufficient institutional structure"
        
        result = {
            "decision": decision,
            "confidence": confidence,
            "score_breakdown": {
                "absorption": absorption_score,
                "sweeps": sweep_score,
                "memory": memory_score,
                "volume": volume_score,
                "structure": integrity_score
            },
            "reasons": reasons,
            "primary_reason": reason,
            "zone_count": len(absorption_zones),
            "sweep_count": len(sweeps)
        }
        
        self.last_decision = result
        self.decision_history.append(result)
        
        return result
    
    def get_decision_quality(self):
        """
        Analyze decision quality over time.
        How often do high-confidence decisions result in successful trades?
        (Requires external outcome tracking)
        """
        if not self.decision_history:
            return None
        
        high_confidence = [d for d in self.decision_history if d["confidence"] >= 0.7]
        
        return {
            "total_decisions": len(self.decision_history),
            "high_confidence_count": len(high_confidence),
            "avg_confidence": sum(d["confidence"] for d in self.decision_history) / len(self.decision_history),
            "last_decision": self.last_decision
        }
    
    def explain_last_decision(self):
        """Return human-readable explanation of last decision."""
        if not self.last_decision:
            return "No decision yet"
        
        d = self.last_decision
        explanation = f"""
        DECISION: {d['decision']} (Confidence: {d['confidence']:.2%})
        
        Primary Reason: {d['primary_reason']}
        
        Score Breakdown:
        - Absorption: {d['score_breakdown']['absorption']:.2f} (institutional volume clusters)
        - Sweeps: {d['score_breakdown']['sweeps']:.2f} (liquidity hunts)
        - Memory: {d['score_breakdown']['memory']:.2f} (session confluence)
        - Volume: {d['score_breakdown']['volume']:.2f} (trade confirmation)
        - Structure: {d['score_breakdown']['structure']:.2f} (bias alignment)
        
        Evidence:
        {chr(10).join(f'  • {r}' for r in d['reasons'])}
        
        Market Data:
        - Active Zones: {d['zone_count']}
        - Traps Detected: {d['sweep_count']}
        """
        return explanation.strip()
