class DecisionLockEngine:
    STATES = ["OBSERVE", "PREPARE", "EXECUTE", "LOCK", "RESET"]

    def __init__(self):
        self.state = "OBSERVE"
        self.trades_this_session = 0
        self.trades_today = 0
        self.final_confidence = 0.0

    def update_state(self, event):
        if event == "start_session":
            self.state = "OBSERVE"
            self.trades_this_session = 0
        elif event == "prepare":
            self.state = "PREPARE"
        elif event == "execute":
            if self.trades_this_session < 1 and self.trades_today < 2 and self.final_confidence >= 0.7:
                self.state = "EXECUTE"
                self.trades_this_session += 1
                self.trades_today += 1
            else:
                self.state = "LOCK"
        elif event == "lock":
            self.state = "LOCK"
        elif event == "reset":
            self.state = "RESET"
            self.trades_this_session = 0
            self.final_confidence = 0.0

    def set_confidence(self, value):
        self.final_confidence = value

    def can_trade(self):
        return self.state == "EXECUTE"

    def fail_safe(self, reason):
        self.state = "LOCK"
        return f"SYSTEM STATUS: PROTECTIVE LOCK\nReason: {reason}\nTrading suspended"
