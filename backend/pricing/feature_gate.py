"""
Feature Gate System
Controls what each subscriber can access based on tier + progression phase.
Enforces tier boundaries + progression unlocks.
"""

from enum import Enum
from backend.mentor.progression_engine import ProgressionEngine, TraderPhase
from backend.pricing.tier_system import SubscriptionTier, PricingModel


class FeatureGate:
    """
    Master gate controller.
    Answers: "Can this user access this feature right now?"
    
    Logic:
    1. Check if tier allows feature
    2. Check if progression phase allows feature
    3. Return combined result
    """
    
    def __init__(self, user_tier: SubscriptionTier, user_phase: TraderPhase):
        """
        Initialize gate with user's tier and phase.
        
        Args:
            user_tier: SubscriptionTier (FREE, BASIC, PRO, ELITE)
            user_phase: TraderPhase (BEGINNER, ASSISTED, SUPERVISED_PRO, FULL_PRO)
        """
        self.tier = user_tier
        self.phase = user_phase
    
    def can_access(self, feature: str) -> bool:
        """
        Check if user can access a feature.
        
        Returns True only if BOTH conditions are met:
        1. Tier allows it
        2. Phase allows it
        """
        tier_allows = PricingModel.is_feature_available(self.tier, feature)
        phase_allows = self._phase_allows(feature)
        
        return tier_allows and phase_allows
    
    def _phase_allows(self, feature: str) -> bool:
        """Check if progression phase allows feature."""
        
        # Phase 1 (BEGINNER) - Ultra conservative
        if self.phase == TraderPhase.BEGINNER:
            allowed = [
                "live_signals",
                "entry_zones",
                "stop_loss",
                "take_profit",
                "market_bias",
                "qmo_phase",
                "simple_explanations",
                "trade_journal",
                "performance_dashboard"
            ]
            return feature in allowed
        
        # Phase 2 (ASSISTED) - Add context
        elif self.phase == TraderPhase.ASSISTED:
            allowed = [
                "live_signals",
                "entry_zones",
                "stop_loss",
                "take_profit",
                "market_bias",
                "qmo_phase",
                "detailed_explanations",
                "liquidity_map",
                "htf_structure",
                "session_context",
                "iceberg_zones",  # Read-only
                "trade_journal",
                "performance_dashboard",
                "condition_analysis",
                "edge_decay_detection",
                "backtesting_engine"
            ]
            return feature in allowed
        
        # Phase 3 (SUPERVISED_PRO) - Add advanced + limited discretion
        elif self.phase == TraderPhase.SUPERVISED_PRO:
            allowed = [
                "live_signals",
                "entry_zones",
                "stop_loss",
                "take_profit",
                "market_bias",
                "qmo_phase",
                "detailed_explanations",
                "liquidity_map",
                "htf_structure",
                "session_context",
                "iceberg_zones",
                "gann_levels",
                "astro_timing",
                "manual_entry_discretion",  # NEW - within zones only
                "trade_journal",
                "performance_dashboard",
                "condition_analysis",
                "edge_decay_detection",
                "backtesting_engine",
                "advanced_dashboard"
            ]
            return feature in allowed
        
        # Phase 4 (FULL_PRO) - Everything
        elif self.phase == TraderPhase.FULL_PRO:
            # All features allowed (tier still applies)
            return True
        
        return False
    
    def get_available_features(self) -> dict:
        """Get all available features for this user."""
        tier_features = PricingModel.get_tier_features(self.tier)
        available = {}
        
        for feature, _ in tier_features.items():
            if self.can_access(feature):
                available[feature] = True
        
        return available
    
    def get_locked_features(self) -> dict:
        """Get features locked by tier or phase."""
        tier_features = PricingModel.get_tier_features(self.tier)
        locked = {}
        
        for feature, _ in tier_features.items():
            if not self.can_access(feature):
                locked[feature] = {
                    "tier_blocks": not PricingModel.is_feature_available(self.tier, feature),
                    "phase_blocks": not self._phase_allows(feature)
                }
        
        return locked
    
    def print_access_summary(self):
        """Print user's feature access."""
        print(f"\n{'='*70}")
        print(f"FEATURE ACCESS — {self.tier.name} Tier | {self.phase.name} Phase")
        print(f"{'='*70}\n")
        
        available = self.get_available_features()
        locked = self.get_locked_features()
        
        print(f"✅ AVAILABLE ({len(available)} features):")
        for feature in sorted(available.keys()):
            print(f"   • {feature}")
        
        print(f"\n❌ LOCKED ({len(locked)} features):")
        for feature, reasons in sorted(locked.items()):
            blocks = []
            if reasons['tier_blocks']:
                blocks.append("Tier")
            if reasons['phase_blocks']:
                blocks.append("Phase")
            print(f"   • {feature} (blocked by: {', '.join(blocks)})")
        
        print(f"\n{'='*70}\n")


class MonetizationFramework:
    """
    Business logic layer.
    Connects pricing to system.
    """
    
    @staticmethod
    def get_user_access(user_tier: SubscriptionTier, user_phase: TraderPhase):
        """Get complete access profile for user."""
        gate = FeatureGate(user_tier, user_phase)
        return {
            "tier": user_tier.name,
            "phase": user_phase.name,
            "price_monthly": PricingModel.get_price(user_tier, annual=False),
            "price_annual": PricingModel.get_price(user_tier, annual=True),
            "available_features": gate.get_available_features(),
            "locked_features": gate.get_locked_features()
        }
    
    @staticmethod
    def should_upsell(user_tier: SubscriptionTier, user_phase: TraderPhase):
        """
        Determine if user should be offered upsell.
        
        Rules:
        - Beginner Phase 1 + 10 trades → Offer BASIC
        - Assisted Phase 2 + 30 trades → Offer PRO
        - Supervised Pro Phase 3+ → Offer ELITE
        """
        
        # Phase advancement → tier upgrade suggestions
        if user_phase == TraderPhase.BEGINNER and user_tier == SubscriptionTier.FREE:
            return {
                "should_offer": True,
                "tier": SubscriptionTier.BASIC,
                "reason": "You've mastered Phase 1. Ready for live execution.",
                "benefit": "Unlock real-time signals + full dashboard"
            }
        
        elif user_phase == TraderPhase.ASSISTED and user_tier == SubscriptionTier.BASIC:
            return {
                "should_offer": True,
                "tier": SubscriptionTier.PRO,
                "reason": "You've progressed to Phase 2. Time for advanced tools.",
                "benefit": "HTF context + Gann/Astro + Backtesting"
            }
        
        elif user_phase in [TraderPhase.SUPERVISED_PRO, TraderPhase.FULL_PRO]:
            if user_tier in [SubscriptionTier.FREE, SubscriptionTier.BASIC, SubscriptionTier.PRO]:
                return {
                    "should_offer": True,
                    "tier": SubscriptionTier.ELITE,
                    "reason": "Full institutional trader. Unlock manual control.",
                    "benefit": "Full override + API + 1-on-1 reviews"
                }
        
        return {"should_offer": False}


# Example usage:
if __name__ == "__main__":
    # Test feature gates for different tiers/phases
    print("\n" + "="*70)
    print("FEATURE GATE TEST — All Tier/Phase Combinations")
    print("="*70)
    
    for tier in SubscriptionTier:
        for phase in TraderPhase:
            gate = FeatureGate(tier, phase)
            print(f"\n{tier.name} + {phase.name}:")
            print(f"  Can access live_signals: {gate.can_access('live_signals')}")
            print(f"  Can access gann_levels: {gate.can_access('gann_levels')}")
            print(f"  Can access manual_override: {gate.can_access('manual_override')}")
            print(f"  Can access api_access: {gate.can_access('api_access')}")
    
    # Test upsell logic
    print("\n" + "="*70)
    print("UPSELL RECOMMENDATIONS")
    print("="*70)
    
    test_cases = [
        (SubscriptionTier.FREE, TraderPhase.BEGINNER),
        (SubscriptionTier.BASIC, TraderPhase.ASSISTED),
        (SubscriptionTier.PRO, TraderPhase.SUPERVISED_PRO),
        (SubscriptionTier.ELITE, TraderPhase.FULL_PRO)
    ]
    
    for tier, phase in test_cases:
        upsell = MonetizationFramework.should_upsell(tier, phase)
        if upsell['should_offer']:
            print(f"\n{tier.name} → {phase.name}")
            print(f"  💰 Upsell to: {upsell['tier'].name}")
            print(f"  💬 Message: {upsell['reason']}")
