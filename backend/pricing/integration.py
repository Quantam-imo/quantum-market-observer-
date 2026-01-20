"""
Pricing Integration Layer
Connects subscription tiers to the trading system.
Dynamically enables/disables features based on tier + phase.
"""

from backend.pricing.tier_system import SubscriptionTier, PricingModel
from backend.pricing.feature_gate import FeatureGate, MonetizationFramework
from backend.mentor.progression_engine import TraderPhase


class PricingIntegration:
    """
    Master integration point.
    Every signal check queries this for tier availability.
    """
    
    def __init__(self, user_tier: SubscriptionTier, user_phase: TraderPhase):
        """Initialize pricing for user."""
        self.tier = user_tier
        self.phase = user_phase
        self.gate = FeatureGate(user_tier, user_phase)
    
    def can_use_mentor_signal(self, signal_data: dict) -> dict:
        """
        Check if user can access a complete mentor signal.
        
        Returns what parts of signal to show.
        """
        result = {
            "can_access": True,
            "components": {},
            "message": ""
        }
        
        # Check core signal access
        if not self.gate.can_access("live_signals"):
            result["can_access"] = False
            result["message"] = "Update to BASIC tier for live signals"
            return result
        
        # Determine what components to show
        signal_components = {
            "direction": self.gate.can_access("entry_zones"),
            "entry": self.gate.can_access("entry_zones"),
            "stop_loss": self.gate.can_access("stop_loss"),
            "targets": self.gate.can_access("take_profit"),
            "confidence": self.gate.can_access("live_signals"),
            "simple_explanation": self.gate.can_access("simple_explanations"),
            "liquidity_map": self.gate.can_access("liquidity_map"),
            "htf_structure": self.gate.can_access("htf_structure"),
            "iceberg_zones": self.gate.can_access("iceberg_zones"),
            "gann_levels": self.gate.can_access("gann_levels"),
            "astro_timing": self.gate.can_access("astro_timing"),
            "manual_override": self.gate.can_access("manual_override")
        }
        
        result["components"] = signal_components
        return result
    
    def format_signal_for_tier(self, full_signal: dict) -> dict:
        """
        Take full signal and format for user's tier.
        Removes locked features.
        """
        access = self.can_use_mentor_signal(full_signal)
        
        if not access["can_access"]:
            return {
                "status": "LOCKED",
                "message": access["message"],
                "upgrade_tier": self._suggest_upgrade()
            }
        
        # Build signal with only accessible components
        formatted = {}
        components = access["components"]
        
        if components.get("direction"):
            formatted["direction"] = full_signal.get("direction")
        
        if components.get("entry"):
            formatted["entry"] = full_signal.get("entry")
        
        if components.get("stop_loss"):
            formatted["stop_loss"] = full_signal.get("stop_loss")
        
        if components.get("targets"):
            formatted["targets"] = full_signal.get("targets")
        
        if components.get("confidence"):
            formatted["confidence"] = full_signal.get("confidence")
        
        if components.get("simple_explanation"):
            formatted["reason"] = full_signal.get("reason")
        
        # Only show advanced info if they have access
        if components.get("liquidity_map"):
            formatted["liquidity"] = full_signal.get("liquidity")
        
        if components.get("htf_structure"):
            formatted["htf_bias"] = full_signal.get("htf_bias")
        
        if components.get("iceberg_zones"):
            formatted["iceberg_zones"] = full_signal.get("iceberg_zones")
        
        if components.get("gann_levels"):
            formatted["gann_levels"] = full_signal.get("gann_levels")
        
        if components.get("astro_timing"):
            formatted["astro_windows"] = full_signal.get("astro_windows")
        
        # Manual override only for elite
        if components.get("manual_override") and full_signal.get("manual_override"):
            formatted["can_override"] = True
        else:
            formatted["can_override"] = False
        
        formatted["tier_note"] = self._get_tier_note()
        
        return formatted
    
    def _suggest_upgrade(self) -> dict:
        """Suggest appropriate upgrade."""
        upsell = MonetizationFramework.should_upsell(self.tier, self.phase)
        
        if upsell['should_offer']:
            return {
                "recommended_tier": upsell['tier'].name,
                "price": PricingModel.get_price(upsell['tier'], annual=False),
                "message": upsell['reason'],
                "benefit": upsell['benefit']
            }
        return {}
    
    def _get_tier_note(self) -> str:
        """Get friendly tier status message."""
        tier_name = PricingModel.TIERS[self.tier]['name']
        
        if self.tier == SubscriptionTier.FREE:
            return f"🟢 {tier_name} tier | Upgrade to BASIC for live signals ($99/mo)"
        elif self.tier == SubscriptionTier.BASIC:
            return f"🟢 {tier_name} tier | Features unlock as you progress"
        elif self.tier == SubscriptionTier.PRO:
            return f"🔵 {tier_name} tier | Advanced tools unlocked"
        elif self.tier == SubscriptionTier.ELITE:
            return f"🟡 {tier_name} tier | Full institutional platform"
    
    def get_ui_permissions(self) -> dict:
        """
        Get UI permission flags.
        Frontend uses these to show/hide buttons.
        """
        return {
            "show_live_signals": self.gate.can_access("live_signals"),
            "show_entry_form": self.gate.can_access("entry_zones"),
            "show_liquidity_map": self.gate.can_access("liquidity_map"),
            "show_gann_panel": self.gate.can_access("gann_levels"),
            "show_astro_panel": self.gate.can_access("astro_timing"),
            "show_override_button": self.gate.can_access("manual_override"),
            "show_backtest_engine": self.gate.can_access("backtesting_engine"),
            "show_api_settings": self.gate.can_access("api_access"),
            "show_performance_analytics": self.gate.can_access("condition_analysis"),
            "tier": self.tier.name,
            "phase": self.phase.name
        }
    
    def get_tier_benefits(self) -> str:
        """Get human-readable tier benefits."""
        tier_data = PricingModel.TIERS[self.tier]
        
        benefits = [
            f"📊 Tier: {tier_data['name']}",
            f"💰 Price: ${tier_data['price_usd_monthly']}/month",
            f"📝 {tier_data['description']}"
        ]
        
        return "\n".join(benefits)


class SignalFormatterWithPricing:
    """
    Example of how to use pricing integration in signal formatting.
    """
    
    @staticmethod
    def create_signal(
        mentor_signal: dict,
        user_tier: SubscriptionTier,
        user_phase: TraderPhase
    ) -> dict:
        """
        Create a signal, applying tier restrictions.
        """
        pricing = PricingIntegration(user_tier, user_phase)
        
        # Check if user can access signals at all
        access = pricing.can_use_mentor_signal(mentor_signal)
        if not access["can_access"]:
            return {
                "status": "BLOCKED",
                "reason": access["message"],
                "upgrade": access.get("upgrade_tier")
            }
        
        # Format signal for this user's tier
        signal = pricing.format_signal_for_tier(mentor_signal)
        
        # Add tier metadata
        signal["metadata"] = {
            "user_tier": user_tier.name,
            "user_phase": user_phase.name,
            "permissions": pricing.get_ui_permissions(),
            "timestamp": mentor_signal.get("timestamp")
        }
        
        return signal


# Example usage:
if __name__ == "__main__":
    # Example signal from mentor
    full_signal = {
        "direction": "SELL",
        "entry": "3365-3370",
        "stop_loss": "3385",
        "targets": ["3345", "3320"],
        "confidence": 0.87,
        "reason": "Institutions liquidating long positions at resistance",
        "liquidity": "400+ contracts absorbed at 3368",
        "htf_bias": "BEARISH",
        "iceberg_zones": ["3372", "3380"],
        "gann_levels": ["3360", "3375"],
        "astro_windows": "Moon square Saturn active",
        "manual_override": False,
        "timestamp": "2026-01-18T14:30:00Z"
    }
    
    print("\n" + "="*70)
    print("SIGNAL FORMATTING BY TIER")
    print("="*70 + "\n")
    
    # Test each tier
    test_cases = [
        (SubscriptionTier.FREE, TraderPhase.BEGINNER),
        (SubscriptionTier.BASIC, TraderPhase.BEGINNER),
        (SubscriptionTier.PRO, TraderPhase.ASSISTED),
        (SubscriptionTier.ELITE, TraderPhase.FULL_PRO)
    ]
    
    for tier, phase in test_cases:
        print(f"\n🟢 {tier.name} + {phase.name}")
        print("-" * 70)
        
        signal = SignalFormatterWithPricing.create_signal(
            full_signal,
            tier,
            phase
        )
        
        # Print what components are shown
        if "direction" in signal:
            print(f"  ✅ Direction: {signal['direction']}")
        if "entry" in signal:
            print(f"  ✅ Entry: {signal['entry']}")
        if "liquidity" in signal:
            print(f"  ✅ Liquidity analysis shown")
        if "gann_levels" in signal:
            print(f"  ✅ Gann levels shown")
        if "can_override" in signal and signal['can_override']:
            print(f"  ✅ Manual override enabled")
        else:
            print(f"  ❌ Manual override locked")
