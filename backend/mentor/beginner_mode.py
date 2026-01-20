"""
Beginner Mode - Simplified trading interface
Filters for only highest-confidence signals
Full system runs underneath, but UI is clean & clear
"""

from backend.intelligence.step3_imo_pipeline import Step3IMOPipeline
from backend.mentor.mentor_brain import MentorBrain
from backend.mentor.confidence_engine import ConfidenceEngine


class BeginnerMode:
    """
    Simplified system for traders new to QMO/IMO/Gann/Astro.
    
    Key principle:
    - Full system still runs behind scenes
    - Only shows signals when VERY confident (80%+)
    - Clear, actionable instructions only
    - No discretion allowed
    """
    
    def __init__(self):
        self.pipeline = Step3IMOPipeline()
        self.mentor = MentorBrain()
        self.confidence_engine = ConfidenceEngine()
        
        # Beginner rules (non-negotiable)
        self.min_confidence = 0.80  # 80% minimum
        self.max_trades_per_session = 1
        self.allowed_sessions = ["NEW_YORK"]
        self.allowed_minutes = 90  # First 90 min of NY only
        self.fixed_risk_pct = 0.25  # 0.25% per trade
        
        self.session_trade_count = 0
        self.today_trades = []
    
    def process_signal(self, tick_data, candle_data, session_info):
        """
        Process signal through full system,
        but only return if beginner-safe.
        
        Args:
            tick_data: CME trade data
            candle_data: OHLC candles
            session_info: Current session info {session, time_into_session}
        
        Returns:
            BeginnerSignal or None
        """
        
        # Step 1: Check if beginner is allowed to trade
        if not self._is_session_allowed(session_info):
            return None
        
        if self.session_trade_count >= self.max_trades_per_session:
            return None
        
        # Step 2: Run full system
        full_decision = self.pipeline.process_tick(tick_data, candle_data)
        
        # Step 3: Filter for beginner safety
        if full_decision["confidence"] < self.min_confidence:
            return None
        
        if full_decision["decision"] not in ["BUY", "SELL"]:
            return None
        
        # Step 4: Create beginner-friendly signal
        beginner_signal = self._create_beginner_signal(full_decision, session_info)
        
        return beginner_signal
    
    def _is_session_allowed(self, session_info):
        """
        Check if current session is allowed for beginners.
        (New York only, first 90 minutes)
        """
        current_session = session_info.get("session", "UNKNOWN")
        minutes_into = session_info.get("minutes_into_session", 999)
        
        if current_session not in self.allowed_sessions:
            return False
        
        if minutes_into > self.allowed_minutes:
            return False
        
        return True
    
    def _create_beginner_signal(self, full_decision, session_info):
        """
        Convert full system decision into beginner-friendly format.
        """
        return {
            "type": "BEGINNER_SIGNAL",
            "direction": full_decision["decision"],
            "confidence": full_decision["confidence"],
            
            # Entry instructions (beginner does not vary)
            "entry_low": full_decision.get("entry_low"),
            "entry_high": full_decision.get("entry_high"),
            "entry_instruction": f"Enter between {full_decision.get('entry_low')} - {full_decision.get('entry_high')}",
            
            # Stop (never to be widened)
            "stop_loss": full_decision.get("stop_loss"),
            "stop_instruction": f"Place stop at {full_decision.get('stop_loss')} (NON-NEGOTIABLE)",
            
            # Targets (no discretion)
            "target_1": full_decision.get("target_1"),
            "target_2": full_decision.get("target_2"),
            "target_instruction": f"Target 1: {full_decision.get('target_1')} (take 50%)\nTarget 2: {full_decision.get('target_2')} (let run)",
            
            # Why? (educational but simple)
            "reasons": self._simplify_reasons(full_decision.get("reasons", [])),
            
            # Action (crystal clear)
            "action": self._get_action_instruction(session_info),
            
            # Risk (pre-calculated)
            "risk_amount": self._calculate_risk(full_decision),
            "position_size": self._calculate_position_size(full_decision)
        }
    
    def _simplify_reasons(self, technical_reasons):
        """
        Convert technical reasons into beginner language.
        """
        simplified = []
        
        for reason in technical_reasons:
            if "absorption" in reason.lower():
                simplified.append("✔ Institutions buying/selling here")
            elif "sweep" in reason.lower():
                simplified.append("✔ Liquidity trapped (institutions hunting stops)")
            elif "gann" in reason.lower():
                simplified.append("✔ Price at important level")
            elif "astro" in reason.lower():
                simplified.append("✔ Time window aligned")
            elif "cycle" in reason.lower():
                simplified.append("✔ Cycle count completed")
        
        return simplified if simplified else ["✔ All systems aligned"]
    
    def _get_action_instruction(self, session_info):
        """
        Crystal clear action for beginner.
        """
        return """
NEXT STEP:
1. Wait for current candle to close
2. Place trade at entry zone
3. Place stop at defined level
4. Set both targets
5. DO NOT TOUCH UNTIL TARGET 1 OR STOP HIT
        """
    
    def _calculate_risk(self, decision):
        """Calculate fixed risk amount."""
        account_size = 10000  # Default assumption, can be configured
        risk_amount = account_size * self.fixed_risk_pct / 100
        return risk_amount
    
    def _calculate_position_size(self, decision):
        """
        Calculate position size based on:
        - Fixed risk (0.25%)
        - Stop distance
        """
        risk = self._calculate_risk(decision)
        stop_distance = abs(decision.get("stop_loss", 0) - decision.get("entry_low", 0))
        
        if stop_distance == 0:
            return 0
        
        position_size = risk / stop_distance
        return round(position_size, 2)
    
    def log_trade(self, trade_data):
        """
        Log a beginner trade (very simple).
        """
        trade = {
            "took_trade": trade_data.get("took_trade", False),
            "followed_rules": trade_data.get("followed_rules", True),
            "result": trade_data.get("result", "PENDING"),
            "emotion": trade_data.get("emotion", "CALM"),
            "notes": trade_data.get("notes", "")
        }
        
        self.today_trades.append(trade)
        
        # Quick feedback
        return self._generate_simple_feedback(trade)
    
    def _generate_simple_feedback(self, trade):
        """
        Very simple feedback for beginner.
        """
        if trade["took_trade"] and trade["followed_rules"]:
            if trade["result"] == "WIN":
                return "✅ Great! You followed the system and won."
            elif trade["result"] == "LOSS":
                return "✅ You followed the system perfectly. Losses happen. Stay disciplined."
            else:
                return "✅ Trade logged. Now wait for resolution."
        else:
            return "⚠️ Did not follow rules. Review and try again tomorrow."
    
    def daily_summary(self):
        """
        End-of-day summary for beginner.
        """
        if not self.today_trades:
            return "No trades today. That's OK! System waits for high-quality setups."
        
        total = len(self.today_trades)
        wins = sum(1 for t in self.today_trades if t["result"] == "WIN")
        losses = sum(1 for t in self.today_trades if t["result"] == "LOSS")
        followed_rules = sum(1 for t in self.today_trades if t["followed_rules"])
        
        print(f"\n{'='*70}")
        print("END OF DAY SUMMARY (BEGINNER)")
        print(f"{'='*70}\n")
        
        print(f"Trades Taken:      {total}")
        print(f"Wins:              {wins}")
        print(f"Losses:            {losses}")
        print(f"Followed Rules:    {followed_rules}/{total}")
        
        if followed_rules == total:
            print("\n✅ PERFECT DAY - You followed all rules!")
        elif followed_rules >= total * 0.9:
            print("\n✅ EXCELLENT - 90%+ rule compliance")
        else:
            print("\n⚠️  Review: Focus on following AI guidance exactly")
        
        print(f"\n{'='*70}\n")


class ProMode:
    """
    Full system with all features.
    For experienced traders who understand all components.
    """
    
    def __init__(self):
        self.pipeline = Step3IMOPipeline()
        self.mentor = MentorBrain()
        self.confidence_engine = ConfidenceEngine()
        
        # Pro can adjust these
        self.min_confidence = 0.60  # Lower threshold
        self.max_trades_per_session = 3  # More flexibility
        self.allowed_sessions = ["ASIA", "LONDON", "NEW_YORK"]  # All sessions
        self.fixed_risk_pct = 0.50  # Can go higher
    
    def process_signal(self, tick_data, candle_data, session_info):
        """
        Full system decision with all details.
        Pro trader makes final call.
        """
        return self.pipeline.process_tick(tick_data, candle_data)


class ModeSelector:
    """
    Allows switching between Beginner and Pro modes.
    """
    
    def __init__(self, mode="BEGINNER"):
        self.mode = mode
        
        if mode == "BEGINNER":
            self.engine = BeginnerMode()
        elif mode == "PRO":
            self.engine = ProMode()
        else:
            raise ValueError("Mode must be BEGINNER or PRO")
    
    def switch_mode(self, new_mode):
        """Switch between modes."""
        if new_mode == "BEGINNER":
            self.engine = BeginnerMode()
            self.mode = "BEGINNER"
            print("✅ Switched to BEGINNER MODE")
        elif new_mode == "PRO":
            self.engine = ProMode()
            self.mode = "PRO"
            print("✅ Switched to PRO MODE")
        else:
            print("⚠️ Invalid mode")
    
    def process(self, tick_data, candle_data, session_info):
        """
        Route to appropriate engine.
        """
        return self.engine.process_signal(tick_data, candle_data, session_info)


# Example usage:
if __name__ == "__main__":
    print("\n" + "="*70)
    print("BEGINNER MODE DEMO")
    print("="*70 + "\n")
    
    # Create beginner mode
    beginner = BeginnerMode()
    
    # Simulate a signal
    mock_decision = {
        "decision": "SELL",
        "confidence": 0.84,
        "entry_low": 3361,
        "entry_high": 3365,
        "stop_loss": 3374,
        "target_1": 3342,
        "target_2": 3318,
        "reasons": ["absorption detected", "liquidity sweep", "gann aligned"]
    }
    
    session_info = {
        "session": "NEW_YORK",
        "minutes_into_session": 45
    }
    
    # Create beginner signal
    beginner_signal = beginner._create_beginner_signal(mock_decision, session_info)
    
    print("🟢 MARKET STATUS: TRADE ALLOWED\n")
    print(f"📍 SETUP FOUND (XAUUSD)\n")
    print(f"DIRECTION: {beginner_signal['direction']}")
    print(f"ENTRY: {beginner_signal['entry_low']} – {beginner_signal['entry_high']}")
    print(f"STOP LOSS: {beginner_signal['stop_loss']}")
    print(f"TARGET 1: {beginner_signal['target_1']}")
    print(f"TARGET 2: {beginner_signal['target_2']}")
    print(f"CONFIDENCE: {beginner_signal['confidence']:.0%}\n")
    
    print(f"WHY THIS TRADE?")
    for reason in beginner_signal['reasons']:
        print(f"{reason}")
    
    print(f"\n{beginner_signal['action']}")
    
    # Log a trade
    print("\n" + "="*70)
    print("LOGGING BEGINNER TRADE")
    print("="*70 + "\n")
    
    feedback = beginner.log_trade({
        "took_trade": True,
        "followed_rules": True,
        "result": "WIN",
        "emotion": "CALM",
        "notes": "Clean execution"
    })
    
    print(feedback)
    
    # Daily summary
    beginner.today_trades.append({"result": "WIN", "followed_rules": True})
    beginner.daily_summary()
