"""
API Routes with Legal Compliance Integration
All signal endpoints route through compliance checks first
"""

from datetime import datetime
from backend.legal.compliance import LegalCompliance
from backend.legal.signal_formatter import LegalSignalFormatter


class ComplianceMiddleware:
    """
    Middleware that enforces legal compliance on all signals.
    Every API endpoint goes through this before returning data.
    """
    
    def __init__(self):
        self.compliance = LegalCompliance()
        self.formatter = LegalSignalFormatter()
    
    def process_signal(self, signal_data: dict, user_id: str = None) -> dict:
        """
        Process signal through compliance checks.
        Returns formatted, legal signal or rejection.
        """
        
        # Step 1: Check user consent
        if user_id:
            consent_status = self.compliance.require_consent_before_signal(user_id)
            if not consent_status["can_proceed"]:
                return {
                    "status": "error",
                    "code": "CONSENT_REQUIRED",
                    "message": "User must accept disclaimer first",
                    "actions": consent_status["required_actions"]
                }
        
        # Step 2: Format signal with legal safety
        formatted_signal = self.formatter.format_for_display(signal_data, user_id)
        
        if formatted_signal.get("status") == "REJECTED":
            # Signal contains unsafe language
            self.compliance._audit_log(
                "SIGNAL_REJECTED",
                user_id or "unknown",
                f"reason={formatted_signal.get('reason')}"
            )
            return formatted_signal
        
        # Step 3: Add legal annotations
        formatted_signal["legal_status"] = "COMPLIANT"
        formatted_signal["disclaimer_required"] = True
        
        # Step 4: Log the signal for audit trail
        self.compliance._audit_log(
            "SIGNAL_ALLOWED",
            user_id or "unknown",
            f"confidence={formatted_signal.get('confidence')},direction={formatted_signal.get('direction')}"
        )
        
        return formatted_signal


# Example API endpoints with compliance:

class SignalAPI:
    """
    Signal API endpoints with full legal compliance.
    """
    
    def __init__(self):
        self.compliance_middleware = ComplianceMiddleware()
    
    def get_qmo_signal(self, user_id: str) -> dict:
        """
        GET /api/signals/qmo
        Returns QMO signal after compliance checks.
        """
        # ... generate raw signal ...
        signal = {
            "direction": "SELL",
            "entry": "3361-3365",
            "stop_loss": "3374",
            "targets": ["3342", "3318"],
            "confidence": 0.84,
            "reasoning": "Distribution phase detected with volume confirmation",
            "source": "QMO"
        }
        
        # Process through compliance
        return self.compliance_middleware.process_signal(signal, user_id)
    
    def get_imo_signal(self, user_id: str) -> dict:
        """
        GET /api/signals/imo
        Returns IMO (liquidity sweep) signal after compliance checks.
        """
        # ... generate raw signal ...
        signal = {
            "direction": "BUY",
            "entry": "3380-3385",
            "stop_loss": "3370",
            "targets": ["3400", "3420"],
            "confidence": 0.78,
            "reasoning": "Liquidity sweep pattern identified with iceberg detection",
            "source": "IMO"
        }
        
        # Process through compliance
        return self.compliance_middleware.process_signal(signal, user_id)
    
    def get_combined_signal(self, user_id: str) -> dict:
        """
        GET /api/signals/combined
        Returns all signals merged after compliance checks.
        """
        # ... generate combined signal ...
        signal = {
            "direction": "SELL",
            "confidence": 0.82,
            "consensus": "3 of 4 engines agree SELL",
            "signals": {
                "qmo": {"direction": "SELL", "confidence": 0.85},
                "imo": {"direction": "SELL", "confidence": 0.78},
                "gann": {"direction": "NEUTRAL", "confidence": 0.65},
                "astro": {"direction": "SELL", "confidence": 0.84}
            }
        }
        
        # Process through compliance
        return self.compliance_middleware.process_signal(signal, user_id)
    
    def record_user_consent(self, user_id: str) -> dict:
        """
        POST /api/legal/consent
        Records user acceptance of disclaimer.
        """
        result = self.compliance_middleware.compliance.record_user_consent(
            user_id,
            "signal_access"
        )
        return {
            "status": "success",
            "message": "User consent recorded",
            "timestamp": result["timestamp"]
        }
    
    def get_disclaimers(self) -> dict:
        """
        GET /api/legal/disclaimers
        Returns all required disclaimers for frontend display.
        """
        compliance = LegalCompliance()
        return {
            "master_disclaimer": compliance.get_master_disclaimer(),
            "signal_disclaimer": compliance.get_signal_disclaimer(),
            "performance_disclaimer": compliance.get_performance_disclaimer(),
            "version": "1.0"
        }
    
    def validate_signal_text(self, text: str) -> dict:
        """
        POST /api/legal/validate
        Validates signal text for safe language.
        """
        compliance = LegalCompliance()
        validation = compliance.validate_signal_text(text)
        return validation
    
    def get_audit_trail(self, user_id: str = None, limit: int = 100) -> dict:
        """
        GET /api/legal/audit-trail
        Returns compliance audit trail for user or admin.
        """
        compliance = LegalCompliance()
        events = compliance.get_audit_trail(limit=limit)
        
        if user_id:
            # Filter to user's events only
            events = [e for e in events if e.get("user_id") == user_id]
        
        return {
            "events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }


# Example frontend integration:

class FrontendIntegration:
    """
    How to integrate compliance into frontend.
    """
    
    @staticmethod
    def show_signal(signal_response: dict):
        """
        Display signal to user with proper disclaimers.
        """
        
        if signal_response.get("status") == "error":
            # Handle errors (consent required, rejected, etc.)
            if signal_response.get("code") == "CONSENT_REQUIRED":
                show_consent_form(signal_response["actions"])
            else:
                show_error(signal_response["message"])
            return
        
        # Signal is safe to display
        print("\n" + "="*60)
        print("SIGNAL")
        print("="*60 + "\n")
        
        print(f"Direction:      {signal_response['direction'].upper()}")
        print(f"Confidence:     {signal_response['confidence']:.0%}")
        print(f"Entry:          {signal_response['entry']}")
        print(f"Stop Loss:      {signal_response['stop_loss']}")
        print(f"Targets:        {', '.join(signal_response['targets'])}")
        
        # Show disclaimer if required
        if signal_response.get("disclaimer_required"):
            print("\n" + "-"*60)
            print(signal_response['disclaimer_text'])
            print("-"*60)
        
        print("\n")
    
    @staticmethod
    def show_disclaimer_on_load():
        """
        Show master disclaimer on app load.
        """
        api = SignalAPI()
        disclaimers = api.get_disclaimers()
        
        print("\n" + "!"*60)
        print(disclaimers["master_disclaimer"])
        print("!"*60 + "\n")
        
        print("By using this platform, you acknowledge:")
        print("  ☐ This is NOT financial advice")
        print("  ☐ You accept all trading risks")
        print("  ☐ You are responsible for your trades")
        print("\nCheck all boxes to continue...")


# Example usage:
if __name__ == "__main__":
    api = SignalAPI()
    
    # User consent first
    print("Recording user consent...")
    consent_result = api.record_user_consent("trader_123")
    print(f"✅ {consent_result['message']}\n")
    
    # Get signal
    print("Getting QMO signal...")
    signal = api.get_qmo_signal("trader_123")
    
    print(f"✅ Signal allowed")
    if signal.get("direction"):
        print(f"Direction: {signal['direction']}")
        print(f"Confidence: {signal.get('confidence', 'N/A'):.0%}")
        print(f"\nWith disclaimer:")
        print(signal.get('disclaimer_text', 'Disclaimer not available'))
    
    # Get audit trail
    print("\n\nAudit Trail:")
    audit = api.get_audit_trail("trader_123", limit=5)
    for event in audit["events"]:
        print(f"  - {event['timestamp']}: {event['event_type']}")
