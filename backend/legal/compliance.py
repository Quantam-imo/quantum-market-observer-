"""
Legal Disclaimer & Regulatory Compliance Framework
Ensures platform is legally positioned as "analytics tool" not "advisor"
Enforces safe language, logs compliance, manages user consent
"""

from datetime import datetime
from enum import Enum
import json


class DisclaimerType(Enum):
    """Types of disclaimers needed."""
    MASTER = 1
    SIGNAL_SPECIFIC = 2
    RISK_WARNING = 3
    PERFORMANCE = 4


class LegalCompliance:
    """
    Master legal compliance controller.
    Every user interaction flows through this.
    """
    
    # MASTER DISCLAIMER (Display everywhere)
    MASTER_DISCLAIMER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                            ⚠️  DISCLAIMER                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

This platform provides market analysis, educational insights, and probabilistic 
trading signals based on historical data, mathematical models, and timing frameworks.

⚠️  CRITICAL LEGAL STATEMENTS:

This is NOT financial advice.
This is NOT investment recommendation.
This platform does NOT guarantee profits.
This platform does NOT manage your account.
This platform does NOT execute your trades.

RISK ACKNOWLEDGMENT:
Trading involves substantial risk of loss of capital.
Past performance does NOT guarantee future results.
Market conditions change. Edge decay is possible.
You may lose all or substantially all of your investment.

YOUR RESPONSIBILITY:
• You alone are responsible for all trading decisions.
• You alone control trade entry and exit.
• You alone assume all financial risk.
• You alone manage position sizing and risk.

PLATFORM LIMITATIONS:
• Signals are probabilistic, not deterministic.
• Confidence scores reflect model consensus, not certainty.
• No historical win rate guarantees future performance.
• System may generate consecutive losses.
• Data feeds may malfunction or delay.

REGULATORY STATEMENT:
This platform is an analytical and educational tool.
It is NOT a registered investment advisor.
It does NOT hold client funds or execute trades.
It provides insights and signal generation only.

Use at your own risk.
By accessing this platform, you accept full responsibility for your trading.

Last Updated: 2026-01-18
"""
    
    # SIGNAL-SPECIFIC DISCLAIMER (Appended to every signal)
    SIGNAL_DISCLAIMER = """
⚠️  This is an analytical view, not financial advice.
    Confidence score reflects model alignment, not profit probability.
    User discretion and risk management required.
"""
    
    # PERFORMANCE DISCLAIMER
    PERFORMANCE_DISCLAIMER = """
⚠️  PERFORMANCE HISTORY DISCLAIMER:

Past performance does NOT indicate future results.
• Backtested performance may not reflect live trading.
• Slippage, commissions, and spreads affect real performance.
• Market structure changes invalidate historical patterns.
• Edge decay is common in systematic strategies.

If you see >50% win rate, be skeptical of over-fitting.
If confidence is always high, be skeptical of reality.
If signals always align, question data quality.

Approach all results with healthy skepticism.
"""
    
    def __init__(self):
        """Initialize compliance system."""
        self.user_consents = {}
        self.audit_log = []
        self.banned_phrases = [
            "buy now", "sell now", "guaranteed", "sure shot",
            "100%", "confirmed", "certain profit", "will make",
            "must trade", "can't miss", "absolute", "definitely"
        ]
        self.required_phrases = [
            "may", "could", "probabilistic", "analysis",
            "confidence", "probability", "educational", "insight"
        ]
    
    def get_master_disclaimer(self) -> str:
        """Get master disclaimer for display."""
        return self.MASTER_DISCLAIMER
    
    def get_signal_disclaimer(self) -> str:
        """Get signal-specific disclaimer."""
        return self.SIGNAL_DISCLAIMER
    
    def get_performance_disclaimer(self) -> str:
        """Get performance history disclaimer."""
        return self.PERFORMANCE_DISCLAIMER
    
    def validate_signal_text(self, signal_text: str) -> dict:
        """
        Validate signal text for banned phrases.
        Returns: {
            "is_safe": bool,
            "violations": [str],
            "warnings": [str]
        }
        """
        violations = []
        warnings = []
        
        text_lower = signal_text.lower()
        
        # Check for banned phrases
        for phrase in self.banned_phrases:
            if phrase in text_lower:
                violations.append(f"Banned phrase detected: '{phrase}'")
        
        # Check for risky language
        if "guarantee" in text_lower:
            violations.append("Word 'guarantee' not allowed")
        if "profit" in text_lower and "high probability" not in text_lower:
            warnings.append("Word 'profit' used without qualifying context")
        if "sure" in text_lower:
            violations.append("Word 'sure' suggests certainty (not allowed)")
        
        # Recommend required phrases if missing
        has_disclaimer_lang = any(phrase in text_lower for phrase in [
            "educational", "analytical", "probabilistic", "confidence",
            "may", "could"
        ])
        if not has_disclaimer_lang:
            warnings.append("Consider adding disclaimer language")
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "text_length": len(signal_text),
            "phrase_count": len(text_lower.split())
        }
    
    def record_user_consent(self, user_id: str, consent_type: str) -> dict:
        """
        Record user acceptance of terms.
        Should be called before user can access signals.
        """
        consent = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "consent_type": consent_type,
            "accepted": True,
            "ip_address": "log_ip_here",  # In production, capture actual IP
            "user_agent": "log_browser_here"  # In production, capture actual browser
        }
        
        self.user_consents[user_id] = consent
        self._audit_log("CONSENT_ACCEPTED", user_id, consent_type)
        
        return consent
    
    def has_user_consented(self, user_id: str) -> bool:
        """Check if user has accepted terms."""
        return user_id in self.user_consents
    
    def require_consent_before_signal(self, user_id: str) -> dict:
        """
        Blocks signal if user hasn't accepted terms.
        Returns: {
            "can_proceed": bool,
            "message": str,
            "required_actions": [str]
        }
        """
        if self.has_user_consented(user_id):
            self._audit_log("SIGNAL_ALLOWED", user_id, "consent_verified")
            return {
                "can_proceed": True,
                "message": "User consent verified",
                "required_actions": []
            }
        else:
            self._audit_log("SIGNAL_BLOCKED", user_id, "no_consent")
            return {
                "can_proceed": False,
                "message": "Must accept disclaimer before viewing signals",
                "required_actions": [
                    "Read master disclaimer",
                    "Check: 'I understand this is analytical tool only'",
                    "Check: 'I accept full responsibility for my trades'",
                    "Check: 'I acknowledge trading risks'"
                ]
            }
    
    def format_legal_signal(self, signal_data: dict) -> dict:
        """
        Format signal with legal disclaimers and safe language.
        Returns signal safe for display.
        """
        # Start with base signal
        legal_signal = {
            "timestamp": datetime.now().isoformat(),
            "disclaimer_version": "1.0",
            "regulatory_classification": "Analytical Insight",
            "legal_status": "Not financial advice"
        }
        
        # Add signal data
        legal_signal.update({
            "direction": signal_data.get("direction"),
            "entry": signal_data.get("entry"),
            "stop_loss": signal_data.get("stop_loss"),
            "targets": signal_data.get("targets"),
            "confidence": signal_data.get("confidence"),
            "reasoning": signal_data.get("reasoning")
        })
        
        # Add legal language
        legal_signal["analytics"] = {
            "this_is_not": [
                "financial advice",
                "investment recommendation",
                "guaranteed profit prediction",
                "personalized guidance"
            ],
            "this_is": [
                "mathematical analysis",
                "educational insight",
                "probabilistic signal",
                "analytical perspective"
            ],
            "user_responsibility": [
                "Verify all signals independently",
                "Manage your own risk",
                "Control position sizing",
                "Accept full responsibility"
            ]
        }
        
        # Append signal disclaimer
        legal_signal["disclaimer"] = self.SIGNAL_DISCLAIMER
        
        return legal_signal
    
    def _audit_log(self, event_type: str, user_id: str, details: str):
        """Log all compliance events."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        self.audit_log.append(log_entry)
        
        # Keep last 10,000 entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
    
    def get_audit_trail(self, user_id: str = None, limit: int = 100) -> list:
        """Get audit trail for compliance review."""
        if user_id:
            user_logs = [log for log in self.audit_log if log["user_id"] == user_id]
            return user_logs[-limit:]
        return self.audit_log[-limit:]
    
    def print_compliance_status(self):
        """Print system compliance status."""
        print("\n" + "="*70)
        print("LEGAL COMPLIANCE STATUS")
        print("="*70 + "\n")
        
        print("✅ DISCLAIMERS:")
        print("   Master disclaimer:        ACTIVE")
        print("   Signal disclaimers:       ACTIVE")
        print("   Performance disclaimers:  ACTIVE")
        
        print("\n✅ USER CONSENT:")
        print(f"   Users who consented:      {len(self.user_consents)}")
        
        print("\n✅ AUDIT TRAIL:")
        print(f"   Events logged:            {len(self.audit_log)}")
        
        recent_events = self.audit_log[-5:] if self.audit_log else []
        if recent_events:
            print("\n   Recent events:")
            for event in recent_events:
                print(f"     {event['timestamp'][:19]} | {event['event_type']:20} | {event['user_id']:15}")
        
        print("\n✅ PHRASE VALIDATION:")
        print(f"   Banned phrases:           {len(self.banned_phrases)}")
        print(f"   Required patterns:        {len(self.required_phrases)}")
        
        print("\n" + "="*70 + "\n")


# Example usage:
if __name__ == "__main__":
    compliance = LegalCompliance()
    
    # Print disclaimers
    print("MASTER DISCLAIMER:")
    print(compliance.get_master_disclaimer())
    
    # Test phrase validation
    print("\n" + "="*70)
    print("SIGNAL TEXT VALIDATION")
    print("="*70 + "\n")
    
    # Good signal
    good_signal = """
    Market conditions favor a sell setup.
    High-probability zone identified.
    Confidence: 82%
    This is an analytical view, not financial advice.
    """
    
    result = compliance.validate_signal_text(good_signal)
    print(f"Good signal validation: {result['is_safe']} ✅")
    if result['violations']:
        print(f"  Violations: {result['violations']}")
    if result['warnings']:
        print(f"  Warnings: {result['warnings']}")
    
    # Bad signal
    print()
    bad_signal = "BUY NOW! Guaranteed profit, 100% sure, can't miss this setup!"
    
    result = compliance.validate_signal_text(bad_signal)
    print(f"Bad signal validation: {result['is_safe']} ❌")
    if result['violations']:
        print(f"  Violations: {result['violations']}")
    
    # Test user consent flow
    print("\n" + "="*70)
    print("USER CONSENT FLOW")
    print("="*70 + "\n")
    
    user_id = "trader_123"
    
    # Try to access signal without consent
    check = compliance.require_consent_before_signal(user_id)
    print(f"Before consent: {check['can_proceed']} ❌")
    print(f"  Message: {check['message']}")
    print(f"  Required: {check['required_actions']}\n")
    
    # Accept consent
    consent = compliance.record_user_consent(user_id, "signal_access")
    print(f"Consent recorded: {consent['timestamp']}\n")
    
    # Try again
    check = compliance.require_consent_before_signal(user_id)
    print(f"After consent: {check['can_proceed']} ✅")
    print(f"  Message: {check['message']}\n")
    
    # Print compliance status
    compliance.print_compliance_status()
