"""
Trader Progression Engine - Multi-phase evolution system
Beginner → Assisted → Supervised Pro → Full Pro
Based on behavior, not just time
"""

from datetime import datetime, timedelta
from enum import Enum


class TraderPhase(Enum):
    """Trader evolution phases."""
    BEGINNER = 1
    ASSISTED = 2
    SUPERVISED_PRO = 3
    FULL_PRO = 4


class ProgressionEngine:
    """
    Manages trader progression through 4 phases.
    Unlocks features based on metrics, not guessing.
    """
    
    def __init__(self):
        self.current_phase = TraderPhase.BEGINNER
        self.start_date = datetime.now()
        self.trades = []
        self.rule_violations = []
        self.emotion_log = []
        
        # Progression criteria
        self.phase_requirements = {
            TraderPhase.BEGINNER: {
                "days_required": 0,
                "trades_required": 0,
                "rule_compliance": 0,
                "max_consecutive_losses": 10
            },
            TraderPhase.ASSISTED: {
                "days_required": 30,
                "trades_required": 10,
                "rule_compliance": 0.90,  # 90%+
                "max_consecutive_losses": 3,
                "revenge_trading": False,
                "equity_curve": "stable"
            },
            TraderPhase.SUPERVISED_PRO: {
                "days_required": 60,
                "trades_required": 30,
                "rule_compliance": 0.95,  # 95%+
                "max_consecutive_losses": 2,
                "revenge_trading": False,
                "equity_curve": "positive",
                "win_rate_min": 0.40
            },
            TraderPhase.FULL_PRO: {
                "days_required": 120,
                "trades_required": 60,
                "rule_compliance": 0.98,  # 98%+
                "max_consecutive_losses": 1,
                "revenge_trading": False,
                "equity_curve": "strongly_positive",
                "win_rate_min": 0.50,
                "monthly_positive": True
            }
        }
    
    def log_trade(self, trade_data):
        """
        Log a trade and check for progression eligibility.
        """
        trade = {
            "timestamp": datetime.now(),
            "result": trade_data.get("result"),
            "followed_rules": trade_data.get("followed_rules", True),
            "emotion": trade_data.get("emotion", "CALM"),
            "r_multiple": trade_data.get("r_multiple", 0)
        }
        
        self.trades.append(trade)
        
        # Track emotions
        if trade["emotion"] in ["FEAR", "GREED"]:
            self.emotion_log.append({
                "timestamp": datetime.now(),
                "emotion": trade["emotion"]
            })
        
        # Track violations
        if not trade["followed_rules"]:
            self.rule_violations.append({
                "timestamp": datetime.now(),
                "trade_num": len(self.trades)
            })
        
        # Check progression eligibility
        self._check_phase_progression()
    
    def _check_phase_progression(self):
        """
        Automatically check if trader qualifies for next phase.
        """
        if self.current_phase == TraderPhase.BEGINNER:
            if self._check_assisted_eligibility():
                self._promote_to_assisted()
        
        elif self.current_phase == TraderPhase.ASSISTED:
            if self._check_supervised_pro_eligibility():
                self._promote_to_supervised_pro()
        
        elif self.current_phase == TraderPhase.SUPERVISED_PRO:
            if self._check_full_pro_eligibility():
                self._promote_to_full_pro()
    
    def _check_assisted_eligibility(self):
        """Check if trader ready for Assisted mode."""
        reqs = self.phase_requirements[TraderPhase.ASSISTED]
        
        days_elapsed = (datetime.now() - self.start_date).days
        if days_elapsed < reqs["days_required"]:
            return False
        
        if len(self.trades) < reqs["trades_required"]:
            return False
        
        compliance = self._calculate_rule_compliance()
        if compliance < reqs["rule_compliance"]:
            return False
        
        if self._has_revenge_trading():
            return False
        
        return True
    
    def _check_supervised_pro_eligibility(self):
        """Check if trader ready for Supervised Pro mode."""
        reqs = self.phase_requirements[TraderPhase.SUPERVISED_PRO]
        
        days_elapsed = (datetime.now() - self.start_date).days
        if days_elapsed < reqs["days_required"]:
            return False
        
        if len(self.trades) < reqs["trades_required"]:
            return False
        
        compliance = self._calculate_rule_compliance()
        if compliance < reqs["rule_compliance"]:
            return False
        
        if self._has_revenge_trading():
            return False
        
        if not self._is_equity_positive():
            return False
        
        if self._calculate_win_rate() < reqs["win_rate_min"]:
            return False
        
        return True
    
    def _check_full_pro_eligibility(self):
        """Check if trader ready for Full Pro mode."""
        reqs = self.phase_requirements[TraderPhase.FULL_PRO]
        
        days_elapsed = (datetime.now() - self.start_date).days
        if days_elapsed < reqs["days_required"]:
            return False
        
        if len(self.trades) < reqs["trades_required"]:
            return False
        
        compliance = self._calculate_rule_compliance()
        if compliance < reqs["rule_compliance"]:
            return False
        
        if self._has_revenge_trading():
            return False
        
        if not self._is_equity_strongly_positive():
            return False
        
        if self._calculate_win_rate() < reqs["win_rate_min"]:
            return False
        
        if not self._is_monthly_positive():
            return False
        
        return True
    
    def _calculate_rule_compliance(self):
        """What percentage of trades followed all rules?"""
        if not self.trades:
            return 0
        
        compliant = sum(1 for t in self.trades if t["followed_rules"])
        return compliant / len(self.trades)
    
    def _has_revenge_trading(self):
        """Did trader revenge trade after losses?"""
        for i in range(len(self.trades) - 1):
            if self.trades[i]["result"] == "LOSS":
                # Check if next trade was emotional (quick re-entry)
                time_diff = (self.trades[i+1]["timestamp"] - self.trades[i]["timestamp"]).total_seconds()
                if time_diff < 600:  # Within 10 minutes
                    return True
        
        return False
    
    def _is_equity_positive(self):
        """Is equity curve positive?"""
        if not self.trades:
            return False
        
        total_r = sum(t.get("r_multiple", 0) for t in self.trades)
        return total_r > 0
    
    def _is_equity_strongly_positive(self):
        """Is equity curve strongly positive (>2R total)?"""
        if not self.trades:
            return False
        
        total_r = sum(t.get("r_multiple", 0) for t in self.trades)
        return total_r > 2.0
    
    def _is_monthly_positive(self):
        """Is trader positive in last month?"""
        one_month_ago = datetime.now() - timedelta(days=30)
        recent_trades = [t for t in self.trades if t["timestamp"] > one_month_ago]
        
        if not recent_trades:
            return False
        
        total_r = sum(t.get("r_multiple", 0) for t in recent_trades)
        return total_r > 0
    
    def _calculate_win_rate(self):
        """What is win rate?"""
        if not self.trades:
            return 0
        
        wins = sum(1 for t in self.trades if t["result"] == "WIN")
        return wins / len(self.trades)
    
    def _promote_to_assisted(self):
        """Promote to Assisted mode."""
        self.current_phase = TraderPhase.ASSISTED
        print("\n" + "="*70)
        print("🟡 PROMOTION TO ASSISTED MODE")
        print("="*70)
        print("\nYou've proven discipline!")
        print("New features unlocked:")
        print("  ✔ Liquidity map (read-only)")
        print("  ✔ HTF/LTF bias display")
        print("  ✔ Session structure visibility")
        print("  ✔ Iceberg zones (read-only)")
        print("\nYou still cannot override AI decisions.")
        print("This phase builds understanding.")
        print("="*70 + "\n")
    
    def _promote_to_supervised_pro(self):
        """Promote to Supervised Pro mode."""
        self.current_phase = TraderPhase.SUPERVISED_PRO
        print("\n" + "="*70)
        print("🟠 PROMOTION TO SUPERVISED PRO MODE")
        print("="*70)
        print("\nYou're ready for controlled discretion!")
        print("New features unlocked:")
        print("  ✔ Gann levels overlay")
        print("  ✔ Astro timing windows")
        print("  ✔ VWAP/Anchored VWAP")
        print("  ✔ Manual entry within AI zones")
        print("  ✔ Custom profit-taking (within AI targets)")
        print("\nAI supervises every decision.")
        print("Deviations are logged and analyzed.")
        print("="*70 + "\n")
    
    def _promote_to_full_pro(self):
        """Promote to Full Pro mode."""
        self.current_phase = TraderPhase.FULL_PRO
        print("\n" + "="*70)
        print("🔴 PROMOTION TO FULL PRO MODE")
        print("="*70)
        print("\nYou've earned independence!")
        print("New features unlocked:")
        print("  ✔ Manual bias override (logged)")
        print("  ✔ Multi-position scaling")
        print("  ✔ Custom risk per trade")
        print("  ✔ Session-to-session planning")
        print("  ✔ Strategy testing sandbox")
        print("  ✔ Full system transparency")
        print("\nAI is now an auditor, not a controller.")
        print("You are fully responsible for your execution.")
        print("="*70 + "\n")
    
    def get_phase_features(self):
        """Return available features for current phase."""
        features = {
            TraderPhase.BEGINNER: {
                "direction": True,
                "entry": True,
                "stop_loss": True,
                "target_1": True,
                "target_2": True,
                "confidence": True,
                "simple_reasons": True,
                
                "liquidity_map": False,
                "htf_bias": False,
                "session_structure": False,
                "iceberg_zones": False,
                "gann_levels": False,
                "astro_timing": False,
                "vwap": False,
                "manual_entry": False,
                "manual_risk": False,
                "multi_position": False
            },
            TraderPhase.ASSISTED: {
                "direction": True,
                "entry": True,
                "stop_loss": True,
                "target_1": True,
                "target_2": True,
                "confidence": True,
                "simple_reasons": True,
                
                "liquidity_map": True,  # NEW
                "htf_bias": True,  # NEW
                "session_structure": True,  # NEW
                "iceberg_zones": True,  # NEW (read-only)
                "gann_levels": False,
                "astro_timing": False,
                "vwap": False,
                "manual_entry": False,
                "manual_risk": False,
                "multi_position": False
            },
            TraderPhase.SUPERVISED_PRO: {
                "direction": True,
                "entry": True,
                "stop_loss": True,
                "target_1": True,
                "target_2": True,
                "confidence": True,
                "simple_reasons": True,
                
                "liquidity_map": True,
                "htf_bias": True,
                "session_structure": True,
                "iceberg_zones": True,
                "gann_levels": True,  # NEW
                "astro_timing": True,  # NEW
                "vwap": True,  # NEW
                "manual_entry": True,  # NEW (within zone)
                "manual_risk": False,
                "multi_position": False
            },
            TraderPhase.FULL_PRO: {
                "direction": True,
                "entry": True,
                "stop_loss": True,
                "target_1": True,
                "target_2": True,
                "confidence": True,
                "simple_reasons": True,
                
                "liquidity_map": True,
                "htf_bias": True,
                "session_structure": True,
                "iceberg_zones": True,
                "gann_levels": True,
                "astro_timing": True,
                "vwap": True,
                "manual_entry": True,
                "manual_risk": True,  # NEW
                "multi_position": True  # NEW
            }
        }
        
        return features[self.current_phase]
    
    def get_progression_status(self):
        """Display current progression with metrics."""
        days_elapsed = (datetime.now() - self.start_date).days
        compliance = self._calculate_rule_compliance()
        win_rate = self._calculate_win_rate()
        total_r = sum(t.get("r_multiple", 0) for t in self.trades)
        
        print(f"\n{'='*70}")
        print(f"PROGRESSION STATUS — {self.current_phase.name}")
        print(f"{'='*70}\n")
        
        print(f"Days Trading:      {days_elapsed}")
        print(f"Total Trades:      {len(self.trades)}")
        print(f"Rule Compliance:   {compliance:.1%}")
        print(f"Win Rate:          {win_rate:.1%}")
        print(f"Total R:           {total_r:.2f}R")
        
        print(f"\n{'NEXT PHASE REQUIREMENTS':-^70}")
        if self.current_phase != TraderPhase.FULL_PRO:
            next_phase = TraderPhase(self.current_phase.value + 1)
            reqs = self.phase_requirements[next_phase]
            
            print(f"Days required:     {reqs['days_required']} (you have {days_elapsed})")
            print(f"Trades required:   {reqs['trades_required']} (you have {len(self.trades)})")
            print(f"Compliance needed: {reqs['rule_compliance']:.0%} (you have {compliance:.1%})")
            
            if self._calculate_win_rate() >= 0.40:
                print(f"Win rate needed:   {reqs.get('win_rate_min', 0):.0%} (you have {win_rate:.1%})")
            
            # Show progress
            print(f"\n{'PROGRESS':-^70}")
            if days_elapsed < reqs['days_required']:
                days_left = reqs['days_required'] - days_elapsed
                print(f"⏳ {days_left} days remaining")
            else:
                print(f"✅ Days requirement met")
            
            if len(self.trades) < reqs['trades_required']:
                trades_left = reqs['trades_required'] - len(self.trades)
                print(f"⏳ {trades_left} trades remaining")
            else:
                print(f"✅ Trades requirement met")
            
            if compliance < reqs['rule_compliance']:
                compliance_points = (reqs['rule_compliance'] - compliance) * 100
                print(f"⏳ Need {compliance_points:.1f}% more compliance")
            else:
                print(f"✅ Compliance requirement met")
        else:
            print("🏆 You have reached Full Pro mode!")
            print("No further progression available.")
        
        print(f"\n{'='*70}\n")
    
    def generate_ai_warning(self):
        """Generate behavioral warnings if needed."""
        warnings = []
        
        # Check for overtrading
        trades_this_session = len([t for t in self.trades if (datetime.now() - t["timestamp"]).days == 0])
        if trades_this_session > 3 and self.current_phase == TraderPhase.BEGINNER:
            warnings.append("⚠️  You've traded 3+ times today. System designed for 1/day. Overtrading risk detected.")
        
        # Check for revenge trading
        if self._has_revenge_trading():
            warnings.append("⚠️  Revenge trading pattern detected. Session locked for 24 hours.")
        
        # Check for emotional trading
        emotional_trades = sum(1 for e in self.emotion_log if (datetime.now() - e["timestamp"]).days == 0)
        if emotional_trades > 1:
            warnings.append("⚠️  Emotional trading detected. Take a break.")
        
        # Check for rule violations
        recent_violations = [v for v in self.rule_violations if (datetime.now() - v["timestamp"]).days == 0]
        if len(recent_violations) > 0:
            warnings.append(f"⚠️  {len(recent_violations)} rule violations today. Review discipline.")
        
        return warnings


# Example usage:
if __name__ == "__main__":
    progression = ProgressionEngine()
    
    print("\n" + "="*70)
    print("PROGRESSION ENGINE DEMO")
    print("="*70 + "\n")
    
    # Simulate 35 days of trading
    for day in range(35):
        # Simulate 1-2 trades per day
        for trade_num in range(1):
            progression.log_trade({
                "result": "WIN" if day % 2 == 0 else "LOSS",
                "followed_rules": True,
                "emotion": "CALM",
                "r_multiple": 1.5 if day % 2 == 0 else -1.0
            })
    
    # Show progression
    progression.get_progression_status()
    
    # Show available features
    print(f"AVAILABLE FEATURES — {progression.current_phase.name}")
    print("="*70)
    features = progression.get_phase_features()
    for feature, available in features.items():
        status = "✅" if available else "❌"
        print(f"{status} {feature}")
