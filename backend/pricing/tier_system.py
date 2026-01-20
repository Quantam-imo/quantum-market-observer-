"""
Pricing & Subscription Tier System
4-tier model: Free → Basic → Pro → Elite
"""

from enum import Enum
from datetime import datetime


class SubscriptionTier(Enum):
    """Available subscription tiers."""
    FREE = 1
    BASIC = 2
    PRO = 3
    ELITE = 4


class PricingModel:
    """
    Defines pricing, features, and access for each tier.
    Designed for sustainable, scalable monetization.
    """
    
    TIERS = {
        SubscriptionTier.FREE: {
            "name": "Observer",
            "price_usd_monthly": 0,
            "price_usd_annual": 0,
            "description": "Education + funnel + trust building",
            
            "features": {
                # Signals & Execution
                "live_signals": False,
                "signal_delay_minutes": 15,  # Delayed by 15-30 min
                "entry_zones": False,
                "stop_loss": False,
                "take_profit": False,
                
                # Market Analysis
                "market_bias": True,  # Bullish/Bearish/No trade
                "qmo_phase": True,  # Market phase info
                "simple_explanations": True,  # Why no trade
                
                # Timeframes
                "timeframes_allowed": ["Daily"],  # Only daily summary
                "instruments_allowed": ["XAUUSD"],
                
                # Advanced Features
                "htf_structure": False,
                "iceberg_zones": False,
                "gann_levels": False,
                "astro_timing": False,
                "manual_override": False,
                
                # Platform
                "max_saved_trades": 0,
                "performance_dashboard": False,
                "trade_journal": False,
                "historical_data": False,
                "api_access": False
            },
            
            "limits": {
                "daily_signals": 1,  # Summary only
                "max_concurrent_observations": 1,
                "historical_days": 0
            },
            
            "support": "Community forum only"
        },
        
        SubscriptionTier.BASIC: {
            "name": "Execution",
            "price_usd_monthly": 99,
            "price_usd_annual": 990,
            "description": "Live AI Mentor + Disciplined execution",
            
            "features": {
                # Signals & Execution
                "live_signals": True,  # Real-time
                "signal_delay_minutes": 0,
                "entry_zones": True,
                "stop_loss": True,
                "take_profit": True,
                
                # Market Analysis
                "market_bias": True,
                "qmo_phase": True,
                "simple_explanations": True,
                
                # Timeframes
                "timeframes_allowed": ["5m", "15m"],  # Execution TFs
                "instruments_allowed": ["XAUUSD"],
                
                # Advanced Features
                "htf_structure": False,  # Read-only in assisted phase
                "iceberg_zones": False,
                "gann_levels": False,
                "astro_timing": False,
                "manual_override": False,  # Locked until progression
                
                # Platform
                "max_saved_trades": 100,
                "performance_dashboard": True,
                "trade_journal": True,
                "historical_data": 30,  # 30 days
                "api_access": False
            },
            
            "limits": {
                "daily_signals": 5,
                "max_concurrent_observations": 1,
                "historical_days": 30
            },
            
            "support": "Email support (48h response)",
            "progression": "Auto-tier to PRO after Phase 2"
        },
        
        SubscriptionTier.PRO: {
            "name": "Assisted",
            "price_usd_monthly": 299,
            "price_usd_annual": 2990,
            "description": "Full AI Mentor + Context + Controlled discretion",
            
            "features": {
                # Signals & Execution
                "live_signals": True,
                "signal_delay_minutes": 0,
                "entry_zones": True,
                "stop_loss": True,
                "take_profit": True,
                
                # Market Analysis
                "market_bias": True,
                "qmo_phase": True,
                "detailed_explanations": True,  # More depth
                "liquidity_map": True,  # NEW
                "htf_structure": True,  # NEW
                "session_context": True,  # NEW
                "iceberg_zones": True,  # NEW (read-only initially)
                
                # Timeframes
                "timeframes_allowed": ["1m", "5m", "15m", "1h"],
                "instruments_allowed": ["XAUUSD"],
                
                # Advanced Features
                "gann_levels": False,  # Unlocked in Phase 3
                "astro_timing": False,  # Unlocked in Phase 3
                "manual_entry_discretion": False,  # Unlocked in Phase 3
                "manual_override": False,
                
                # Platform
                "max_saved_trades": 500,
                "performance_dashboard": True,
                "trade_journal": True,
                "condition_analysis": True,  # Win rates by setup
                "edge_decay_detection": True,
                "historical_data": 90,
                "backtesting_engine": True,  # NEW
                "api_access": False
            },
            
            "limits": {
                "daily_signals": 10,
                "max_concurrent_observations": 2,
                "historical_days": 90,
                "backtests_per_month": 20
            },
            
            "support": "Email + Slack community",
            "progression": "Auto-tier to ELITE after Phase 3"
        },
        
        SubscriptionTier.ELITE: {
            "name": "Institutional",
            "price_usd_monthly": 799,
            "price_usd_annual": 7990,
            "description": "Full system + Manual control + Advanced tools",
            
            "features": {
                # Signals & Execution
                "live_signals": True,
                "signal_delay_minutes": 0,
                "entry_zones": True,
                "stop_loss": True,
                "take_profit": True,
                
                # Market Analysis
                "market_bias": True,
                "qmo_phase": True,
                "detailed_explanations": True,
                "liquidity_map": True,
                "htf_structure": True,
                "session_context": True,
                "iceberg_zones": True,
                "gann_levels": True,  # NEW
                "astro_timing": True,  # NEW
                
                # Timeframes
                "timeframes_allowed": ["1m", "5m", "15m", "1h", "4h"],
                "instruments_allowed": ["XAUUSD", "GBPUSD", "EURUSD"],  # Multiple
                
                # Advanced Features
                "manual_entry_discretion": True,  # NEW
                "manual_override": True,  # NEW
                "multi_position_scaling": True,  # NEW
                "custom_risk_sizing": True,  # NEW
                "strategy_sandbox": True,  # NEW
                
                # Platform
                "max_saved_trades": "Unlimited",
                "performance_dashboard": True,
                "advanced_dashboard": True,  # NEW
                "trade_journal": True,
                "condition_analysis": True,
                "edge_decay_detection": True,
                "historical_data": "All",  # Unlimited
                "backtesting_engine": True,
                "api_access": True,  # NEW
                "white_label_ready": True  # NEW
            },
            
            "limits": {
                "daily_signals": "Unlimited",
                "max_concurrent_observations": "Unlimited",
                "historical_days": "All",
                "backtests_per_month": "Unlimited",
                "api_calls_per_day": 10000
            },
            
            "support": "Priority email + Phone + Private Slack channel",
            "bonus_features": [
                "Monthly 1-on-1 review",
                "Early access to new features",
                "Custom indicator development",
                "B2B licensing available"
            ]
        }
    }
    
    @staticmethod
    def get_tier_features(tier: SubscriptionTier):
        """Get all features for a tier."""
        return PricingModel.TIERS[tier]["features"]
    
    @staticmethod
    def get_price(tier: SubscriptionTier, annual: bool = False):
        """Get price for tier."""
        tier_data = PricingModel.TIERS[tier]
        if annual:
            return tier_data["price_usd_annual"]
        return tier_data["price_usd_monthly"]
    
    @staticmethod
    def is_feature_available(tier: SubscriptionTier, feature: str) -> bool:
        """Check if feature is available for tier."""
        features = PricingModel.get_tier_features(tier)
        return features.get(feature, False)
    
    @staticmethod
    def print_pricing_table():
        """Print human-readable pricing comparison."""
        print("\n" + "="*100)
        print("PRICING TIERS — Quantum Market Observer")
        print("="*100 + "\n")
        
        for tier in SubscriptionTier:
            data = PricingModel.TIERS[tier]
            print(f"🟢 {data['name'].upper()}")
            print(f"   ${data['price_usd_monthly']}/month | ${data['price_usd_annual']}/year")
            print(f"   {data['description']}\n")
            
            print(f"   Core Features:")
            print(f"     {'Live signals:' :<30} {data['features']['live_signals']}")
            print(f"     {'Entry/SL/TP:' :<30} {data['features']['entry_zones']}")
            print(f"     {'Timeframes:' :<30} {', '.join(data['features']['timeframes_allowed'])}")
            print(f"     {'HTF context:' :<30} {data['features']['htf_structure']}")
            print(f"     {'Gann/Astro:' :<30} {data['features']['gann_levels']}")
            print(f"     {'Manual override:' :<30} {data['features']['manual_override']}")
            print(f"     {'API access:' :<30} {data['features']['api_access']}")
            print(f"\n   Support: {data['support']}\n")
        
        print("="*100 + "\n")
    
    @staticmethod
    def get_upgrade_path():
        """Show upgrade path based on progression."""
        print("\n" + "="*70)
        print("AUTOMATIC UPGRADE PATH")
        print("="*70 + "\n")
        
        print("Beginner Phase 1 → FREE tier")
        print("  (until you're ready for live trading)\n")
        
        print("Beginner Phase 1 (complete) → BASIC tier")
        print("  $99/month | Full live signals + execution\n")
        
        print("Assisted Phase 2 (complete) → PRO tier")
        print("  $299/month | HTF context + backtesting\n")
        
        print("Supervised Pro Phase 3+ → ELITE tier")
        print("  $799/month | Full manual control + API\n")
        
        print("="*70 + "\n")


# Example usage:
if __name__ == "__main__":
    # Print pricing table
    PricingModel.print_pricing_table()
    
    # Print upgrade path
    PricingModel.get_upgrade_path()
    
    # Check feature availability
    print("\nFEATURE AVAILABILITY MATRIX")
    print("="*70)
    
    features_to_check = [
        "live_signals",
        "entry_zones",
        "manual_override",
        "gann_levels",
        "api_access"
    ]
    
    print(f"\n{'Feature':<25} FREE     BASIC    PRO      ELITE")
    print("-" * 70)
    
    for feature in features_to_check:
        free_avail = PricingModel.is_feature_available(SubscriptionTier.FREE, feature)
        basic_avail = PricingModel.is_feature_available(SubscriptionTier.BASIC, feature)
        pro_avail = PricingModel.is_feature_available(SubscriptionTier.PRO, feature)
        elite_avail = PricingModel.is_feature_available(SubscriptionTier.ELITE, feature)
        
        free_str = "✅" if free_avail else "❌"
        basic_str = "✅" if basic_avail else "❌"
        pro_str = "✅" if pro_avail else "❌"
        elite_str = "✅" if elite_avail else "❌"
        
        print(f"{feature:<25} {free_str}       {basic_str}       {pro_str}       {elite_str}")
