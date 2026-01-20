"""
Legal-Safe Signal Formatter
Converts raw signals into legally compliant format
Enforces safe language, adds disclaimers, validates phrases
"""

from backend.legal.compliance import LegalCompliance


class LegalSignalFormatter:
    """
    Formats signals with legal disclaimers and safe language.
    Every signal goes through this before reaching frontend.
    """
    
    def __init__(self):
        """Initialize with compliance rules."""
        self.compliance = LegalCompliance()
    
    def format_for_display(self, signal_data: dict, user_id: str = None) -> dict:
        """
        Format signal for safe frontend display.
        Adds all required disclaimers and validates language.
        """
        
        # Check user consent if user_id provided
        if user_id:
            consent_check = self.compliance.require_consent_before_signal(user_id)
            if not consent_check["can_proceed"]:
                return {
                    "status": "BLOCKED",
                    "reason": "User consent required",
                    "actions": consent_check["required_actions"]
                }
        
        # Start with legal signal
        formatted = self.compliance.format_legal_signal(signal_data)
        
        # Validate reasoning text for banned phrases
        reasoning = signal_data.get("reasoning", "")
        if reasoning:
            validation = self.compliance.validate_signal_text(reasoning)
            
            if not validation["is_safe"]:
                # Return safe version with warnings
                return {
                    "status": "REJECTED",
                    "reason": "Signal text contains unsafe language",
                    "violations": validation["violations"],
                    "original_signal": formatted
                }
            
            if validation["warnings"]:
                formatted["warnings"] = validation["warnings"]
        
        # Add required disclaimers
        formatted["show_disclaimer"] = True
        formatted["disclaimer_text"] = self.compliance.get_signal_disclaimer()
        
        return formatted
    
    def create_safe_signal(self, 
                          direction: str,
                          entry: str,
                          stop_loss: str,
                          targets: list,
                          confidence: float,
                          reasoning: str) -> dict:
        """
        Create a signal from scratch with legal safety.
        """
        signal = {
            "direction": direction,
            "entry": entry,
            "stop_loss": stop_loss,
            "targets": targets,
            "confidence": confidence,
            "reasoning": reasoning
        }
        
        # Format and return
        return self.format_for_display(signal)
    
    def print_legal_signal_example(self):
        """Print example of legally-safe signal."""
        print("\n" + "="*70)
        print("LEGALLY-SAFE SIGNAL EXAMPLE")
        print("="*70 + "\n")
        
        example_signal = self.create_safe_signal(
            direction="SELL",
            entry="3361-3365",
            stop_loss="3374",
            targets=["3342", "3318"],
            confidence=0.84,
            reasoning="""
Market analysis suggests:
- Distribution phase identified (probabilistic)
- Liquidity sweep pattern observed
- Confluence of technical levels
- Confidence: 84%

This is an analytical perspective, not investment advice.
Risk management and position sizing required.
            """
        )
        
        print(f"Direction:      {example_signal['direction']}")
        print(f"Entry:          {example_signal['entry']}")
        print(f"Stop Loss:      {example_signal['stop_loss']}")
        print(f"Targets:        {example_signal['targets']}")
        print(f"Confidence:     {example_signal['confidence']:.1%}")
        print(f"Legal Status:   {example_signal['legal_status']}")
        print(f"Classification: {example_signal['regulatory_classification']}")
        
        print(f"\nDisclaimer:")
        print(example_signal['disclaimer_text'])
        
        print("="*70 + "\n")


# Example usage:
if __name__ == "__main__":
    formatter = LegalSignalFormatter()
    
    # Print example
    formatter.print_legal_signal_example()
    
    # Test with user consent
    print("\nTESTING WITH USER CONSENT:\n")
    
    user_id = "user_123"
    formatter.compliance.record_user_consent(user_id, "signal_access")
    
    signal = formatter.format_for_display({
        "direction": "BUY",
        "entry": "3380-3385",
        "stop_loss": "3370",
        "targets": ["3400", "3420"],
        "confidence": 0.75,
        "reasoning": "High-probability setup identified. Confidence: 75%"
    }, user_id=user_id)
    
    print(f"Signal status: {signal.get('status', 'OK')}")
    print(f"Direction: {signal.get('direction')}")
    print(f"Confidence: {signal.get('confidence'):.1%}")
